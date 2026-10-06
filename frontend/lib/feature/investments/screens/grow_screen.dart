import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../dashboard/models/dashboard_models.dart';
import '../../dashboard/providers/dashboard_provider.dart';
import '../models/investment_models.dart';
import '../services/investment_service.dart';

class GrowScreen extends ConsumerStatefulWidget {
  const GrowScreen({super.key});

  @override
  ConsumerState<GrowScreen> createState() => _GrowScreenState();
}

class _GrowScreenState extends ConsumerState<GrowScreen> {
  List<InvestmentProductModel> _products = [];
  List<InvestmentRequestModel> _requests = [];
  List<InvestmentTransactionModel> _transactions = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final productsFuture = InvestmentService.getProducts();
      final requestsFuture = InvestmentService.getRequests();
      final transactionsFuture = InvestmentService.getTransactions();
      final results = await Future.wait<dynamic>([
        productsFuture,
        requestsFuture,
        transactionsFuture,
      ]);
      await ref.read(dashboardProvider.notifier).refreshDashboard();
      if (!mounted) return;
      setState(() {
        _products = results[0] as List<InvestmentProductModel>;
        _requests = results[1] as List<InvestmentRequestModel>;
        _transactions = results[2] as List<InvestmentTransactionModel>;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _openRequest(
    InvestmentProductModel product,
    GrowSummary grow,
  ) async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => _InvestmentRequestSheet(
        product: product,
        allocations: grow.allocations,
      ),
    );
    if (created == true) {
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Investment request sent for review.')),
      );
    }
  }

  List<Widget> _productCatalog(GrowSummary? grow) => [
    const _SectionHeading(
      title: 'Choose an investment',
      subtitle: 'Select a product to see its return estimate and invest',
    ),
    const SizedBox(height: 12),
    if (_loading && _products.isEmpty)
      const Center(child: CircularProgressIndicator())
    else if (_products.isEmpty)
      const _EmptyCard(
        icon: Icons.trending_up,
        text:
            'No investment products are available. Refresh or contact support.',
      )
    else
      ..._products.map(
        (product) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: _ProductCard(
            product: product,
            canInvest:
                grow?.allocations.any(
                  (allocation) => allocation.available >= product.minimumAmount,
                ) ??
                false,
            onTap: grow == null ? null : () => _openRequest(product, grow),
          ),
        ),
      ),
    if (grow != null && grow.available <= 0)
      const Padding(
        padding: EdgeInsets.only(top: 2),
        child: Text(
          'There is no uncommitted Grow allocation available to invest.',
          style: TextStyle(fontSize: 12, color: Color(0xFF697586)),
        ),
      ),
    const SizedBox(height: 20),
  ];

  @override
  Widget build(BuildContext context) {
    final dashboard = ref.watch(dashboardProvider);
    final grow = dashboard.value?.grow;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Grow'),
        actions: [
          IconButton(
            tooltip: 'Refresh investments',
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _loading && grow == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                children: [
                  const Text(
                    'Grow your money',
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF281F1F),
                    ),
                  ),
                  const SizedBox(height: 7),
                  const Text(
                    'Explore investment options for your Grow allocation.',
                    style: TextStyle(color: Color(0xFF697586)),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 16),
                    _ErrorCard(message: _error!, onRetry: _load),
                  ],
                  if (grow != null) ...[
                    const SizedBox(height: 22),
                    _PortfolioCard(grow: grow),
                    const SizedBox(height: 24),
                    ..._productCatalog(grow),
                    const SizedBox(height: 26),
                    const _SectionHeading(
                      title: 'My investments',
                      subtitle: 'Active accounts and estimated returns',
                    ),
                    const SizedBox(height: 12),
                    if (grow.accounts.isEmpty)
                      const _EmptyCard(
                        icon: Icons.account_balance_outlined,
                        text: 'Completed investments will appear here.',
                      )
                    else
                      ...grow.accounts.map(
                        (account) => Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: _AccountCard(account: account),
                        ),
                      ),
                    const SizedBox(height: 18),
                    const _SectionHeading(
                      title: 'Your requests',
                      subtitle: 'Track requests awaiting review or completion',
                    ),
                    const SizedBox(height: 12),
                    if (_requests.isEmpty)
                      const _EmptyCard(
                        icon: Icons.receipt_long_outlined,
                        text: 'You have not requested an investment yet.',
                      )
                    else
                      ..._requests.map(
                        (request) => Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: _RequestCard(request: request),
                        ),
                      ),
                    const SizedBox(height: 18),
                    const _SectionHeading(
                      title: 'Activity',
                      subtitle: 'Contributions and other account transactions',
                    ),
                    const SizedBox(height: 12),
                    if (_transactions.isEmpty)
                      const _EmptyCard(
                        icon: Icons.swap_horiz,
                        text: 'Investment activity will appear here after a request is completed.',
                      )
                    else
                      ..._transactions.map(
                        (transaction) => Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: _TransactionCard(transaction: transaction),
                        ),
                      ),
                    const SizedBox(height: 18),
                  ],
                  if (grow == null) ..._productCatalog(null),
                  const SizedBox(height: 20),
                  const Text(
                    'Rates and returns shown for demo products are illustrative only and are not guaranteed.',
                    style: TextStyle(
                      fontSize: 11,
                      height: 1.4,
                      color: Color(0xFF7C8796),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

class _PortfolioCard extends StatelessWidget {
  final GrowSummary grow;

  const _PortfolioCard({required this.grow});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF302323),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'INVESTMENT PORTFOLIO',
            style: TextStyle(
              color: Color(0xFFD9CACA),
              fontSize: 11,
              letterSpacing: 1.1,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'RWF ${formatMoney(grow.investmentBalance)}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 26,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Estimated return: RWF ${formatMoney(grow.projectedReturn)}',
            style: const TextStyle(color: Color(0xFFE6DCDC), fontSize: 13),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              _PortfolioMetric(label: 'Available', value: grow.available),
              _PortfolioMetric(label: 'Reserved', value: grow.reserved),
              _PortfolioMetric(label: 'Invested', value: grow.invested),
            ],
          ),
        ],
      ),
    );
  }
}

class _PortfolioMetric extends StatelessWidget {
  final String label;
  final int value;

  const _PortfolioMetric({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(color: Color(0xFFD9CACA), fontSize: 11),
          ),
          const SizedBox(height: 4),
          Text(
            formatMoney(value),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  final InvestmentProductModel product;
  final bool canInvest;
  final VoidCallback? onTap;

  const _ProductCard({
    required this.product,
    required this.canInvest,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: Color(0xFFECE7E7)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const CircleAvatar(
                  backgroundColor: Color(0xFFFFE8E5),
                  foregroundColor: Color(0xFFDC2626),
                  child: Icon(Icons.trending_up),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        product.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        product.partnerName,
                        style: const TextStyle(
                          color: Color(0xFF697586),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                if (product.name.contains('(Demo)')) const _DemoTag(),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              product.description,
              style: const TextStyle(
                color: Color(0xFF536070),
                height: 1.4,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _InfoChip(
                  label:
                      '${product.annualRate.toStringAsFixed(1)}% indicative / year',
                ),
                _InfoChip(label: '${product.termMonths} months'),
                _InfoChip(label: '${product.riskLevel.toLowerCase()} risk'),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Minimum RWF ${formatMoney(product.minimumAmount)}',
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                    ),
                  ),
                ),
                FilledButton(
                  onPressed: onTap == null || !canInvest ? null : onTap,
                  child: const Text('Invest'),
                ),
              ],
            ),
            if (!canInvest)
              Padding(
                padding: const EdgeInsets.only(top: 7),
                child: Text(
                  'At least RWF ${formatMoney(product.minimumAmount)} available is needed.',
                  style: const TextStyle(
                    color: Color(0xFF7C8796),
                    fontSize: 11,
                  ),
                ),
              ),
            if (product.riskInformation.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                product.riskInformation,
                style: const TextStyle(
                  color: Color(0xFF7C8796),
                  fontSize: 11,
                  height: 1.35,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _InvestmentRequestSheet extends StatefulWidget {
  final InvestmentProductModel product;
  final List<GrowAllocationSummary> allocations;

  const _InvestmentRequestSheet({
    required this.product,
    required this.allocations,
  });

  @override
  State<_InvestmentRequestSheet> createState() =>
      _InvestmentRequestSheetState();
}

class _InvestmentRequestSheetState extends State<_InvestmentRequestSheet> {
  late final TextEditingController _amountController;
  String? _allocationId;
  bool _submitting = false;
  String? _error;

  List<GrowAllocationSummary> get _eligible => widget.allocations
      .where((item) => item.available >= widget.product.minimumAmount)
      .toList();

  GrowAllocationSummary? _selectedAllocation() {
    for (final allocation in _eligible) {
      if (allocation.id == _allocationId) return allocation;
    }
    return null;
  }

  @override
  void initState() {
    super.initState();
    _amountController = TextEditingController(
      text: widget.product.minimumAmount.toString(),
    );
    if (_eligible.isNotEmpty) _allocationId = _eligible.first.id;
  }

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final amount = int.tryParse(_amountController.text.trim());
    final selected = _selectedAllocation();
    if (selected == null) {
      setState(
        () => _error = 'Choose an allocation with enough available Grow funds.',
      );
      return;
    }
    if (amount == null || amount < widget.product.minimumAmount) {
      setState(
        () => _error =
            'Enter at least RWF ${formatMoney(widget.product.minimumAmount)}.',
      );
      return;
    }
    if (amount > selected.available) {
      setState(
        () => _error =
            'This allocation has RWF ${formatMoney(selected.available)} available.',
      );
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await InvestmentService.submitRequest(
        allocationId: selected.id,
        productId: widget.product.id,
        amount: amount,
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final selected = _selectedAllocation();
    final amount = int.tryParse(_amountController.text) ?? 0;
    final estimatedReturn =
        (amount * widget.product.annualRate * widget.product.termMonths / 1200)
            .round();
    final projectedValue = amount + estimatedReturn;
    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        12,
        20,
        20 + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFFD8D1D1),
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
            ),
            const SizedBox(height: 18),
            Text(
              'Request an investment',
              style: Theme.of(context).textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 5),
            Text(
              widget.product.name,
              style: const TextStyle(color: Color(0xFF697586)),
            ),
            const SizedBox(height: 18),
            if (_eligible.isEmpty)
              const _EmptyCard(
                icon: Icons.savings_outlined,
                text: 'No Grow allocation has enough available funds for this product.',
              )
            else ...[
              const Text(
                'Fund this request from',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _allocationId,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
                items: _eligible
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          'Available RWF ${formatMoney(item.available)}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _allocationId = value),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: 'Investment amount (RWF)',
                  helperText:
                      'Minimum RWF ${formatMoney(widget.product.minimumAmount)}${selected == null ? '' : ' | Available RWF ${formatMoney(selected.available)}'}',
                  border: const OutlineInputBorder(),
                ),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF4F2),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Estimated projected return',
                      style: Theme.of(context).textTheme.labelMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'RWF ${formatMoney(estimatedReturn)}',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Projected value after ${widget.product.termMonths} months: '
                      'RWF ${formatMoney(projectedValue)}. This estimate uses '
                      'a simple annual-rate calculation; actual returns may differ.',
                      style: const TextStyle(height: 1.4, fontSize: 12),
                    ),
                  ],
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Color(0xFFB42318))),
              ],
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: FilledButton(
                  onPressed: _submitting || _eligible.isEmpty ? null : _submit,
                  child: _submitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Send investment request'),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your request is reviewed by the MasterSave team before funds are invested.',
                style: TextStyle(
                  color: Color(0xFF697586),
                  fontSize: 11,
                  height: 1.35,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _AccountCard extends StatelessWidget {
  final InvestmentAccountSummary account;

  const _AccountCard({required this.account});

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.account_balance, color: Color(0xFFDC2626)),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  account.productName,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              _StatusTag(status: account.status),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            account.partnerName,
            style: const TextStyle(color: Color(0xFF697586), fontSize: 12),
          ),
          const SizedBox(height: 10),
          Text(
            'Balance  RWF ${formatMoney(account.balance)}',
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            'Principal RWF ${formatMoney(account.principal)} | ${account.annualRate.toStringAsFixed(1)}% indicative',
            style: const TextStyle(color: Color(0xFF697586), fontSize: 12),
          ),
          if (account.maturityDate != null) ...[
            const SizedBox(height: 4),
            Text(
              'Matures ${account.maturityDate!.toIso8601String().substring(0, 10)}',
              style: const TextStyle(color: Color(0xFF697586), fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}

class _RequestCard extends StatelessWidget {
  final InvestmentRequestModel request;

  const _RequestCard({required this.request});

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Row(
        children: [
          const CircleAvatar(
            backgroundColor: Color(0xFFFFE8E5),
            foregroundColor: Color(0xFFDC2626),
            child: Icon(Icons.receipt_long_outlined),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  request.productName.isEmpty
                      ? 'Investment request'
                      : request.productName,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 4),
                Text(
                  '${request.reference} | RWF ${formatMoney(request.amount)}',
                  style: const TextStyle(
                    color: Color(0xFF697586),
                    fontSize: 11,
                  ),
                ),
                if (request.rejectionReason.isNotEmpty) ...[
                  const SizedBox(height: 5),
                  Text(
                    request.rejectionReason,
                    style: const TextStyle(
                      color: Color(0xFFB42318),
                      fontSize: 12,
                    ),
                  ),
                ],
              ],
            ),
          ),
          _StatusTag(status: request.status),
        ],
      ),
    );
  }
}

class _TransactionCard extends StatelessWidget {
  final InvestmentTransactionModel transaction;

  const _TransactionCard({required this.transaction});

  @override
  Widget build(BuildContext context) {
    final date = transaction.occurredAt;
    final dateText = date == null
        ? ''
        : '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
    return _SurfaceCard(
      child: Row(
        children: [
          const CircleAvatar(
            backgroundColor: Color(0xFFEAF7F0),
            foregroundColor: Color(0xFF067647),
            child: Icon(Icons.swap_horiz),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  transaction.description.isEmpty
                      ? transaction.type.replaceAll('_', ' ')
                      : transaction.description,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 4),
                Text(
                  '${transaction.productName} | ${transaction.status}${dateText.isEmpty ? '' : ' | $dateText'}',
                  style: const TextStyle(
                    color: Color(0xFF697586),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            'RWF ${formatMoney(transaction.amount)}',
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _StatusTag extends StatelessWidget {
  final String status;

  const _StatusTag({required this.status});

  @override
  Widget build(BuildContext context) {
    final successful = status == 'ACTIVE' || status == 'COMPLETED';
    final failed = status == 'REJECTED';
    final color = successful
        ? const Color(0xFF067647)
        : failed
        ? const Color(0xFFB42318)
        : const Color(0xFFB54708);
    final background = successful
        ? const Color(0xFFECFDF3)
        : failed
        ? const Color(0xFFFEF3F2)
        : const Color(0xFFFFF4E5);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        status.replaceAll('_', ' '),
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _SectionHeading extends StatelessWidget {
  final String title;
  final String subtitle;

  const _SectionHeading({required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 3),
        Text(
          subtitle,
          style: const TextStyle(color: Color(0xFF697586), fontSize: 12),
        ),
      ],
    );
  }
}

class _SurfaceCard extends StatelessWidget {
  final Widget child;

  const _SurfaceCard({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: const Color(0xFFECE7E7)),
        borderRadius: BorderRadius.circular(17),
      ),
      child: child,
    );
  }
}

class _EmptyCard extends StatelessWidget {
  final IconData icon;
  final String text;

  const _EmptyCard({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF8A7474)),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: Color(0xFF697586), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorCard({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(message, style: const TextStyle(color: Color(0xFFB42318))),
          TextButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final String label;

  const _InfoChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFFF5F2F2),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _DemoTag extends StatelessWidget {
  const _DemoTag();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFFFE8E5),
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Text(
        'DEMO',
        style: TextStyle(
          color: Color(0xFFB42318),
          fontSize: 9,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}
