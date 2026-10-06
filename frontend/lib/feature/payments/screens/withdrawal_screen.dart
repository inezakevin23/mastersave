import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../dashboard/models/dashboard_models.dart';
import '../../dashboard/providers/dashboard_provider.dart';
import '../services/payment_service.dart';

class WithdrawalScreen extends ConsumerStatefulWidget {
  const WithdrawalScreen({super.key});

  @override
  ConsumerState<WithdrawalScreen> createState() => _WithdrawalScreenState();
}

class _WithdrawalScreenState extends ConsumerState<WithdrawalScreen> {
  final _amountController = TextEditingController();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bankCodeController = TextEditingController();
  final _branchCodeController = TextEditingController();
  final _accountController = TextEditingController();

  String? _selectedBucketId;
  String _method = 'MOBILE_MONEY';
  String _network = 'MTN';
  bool _submitting = false;

  @override
  void dispose() {
    _amountController.dispose();
    _nameController.dispose();
    _phoneController.dispose();
    _bankCodeController.dispose();
    _branchCodeController.dispose();
    _accountController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Withdraw savings')),
      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
        data: (data) {
          final eligibleBuckets = data.save.buckets
              .where((bucket) => !bucket.isLocked && bucket.balance > 0)
              .toList();

          if (eligibleBuckets.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'You currently have no savings available for withdrawal.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          final selectedBucket = eligibleBuckets.firstWhere(
            (bucket) => bucket.id == _selectedBucketId,
            orElse: () => eligibleBuckets.first,
          );

          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(
                'Receive your money',
                style: Theme.of(context).textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              const Text(
                'Choose an eligible savings balance and where you want the money sent.',
                style: TextStyle(color: Color(0xFF697586), height: 1.5),
              ),
              const SizedBox(height: 24),
              DropdownButtonFormField<String>(
                initialValue: selectedBucket.id,
                decoration: const InputDecoration(labelText: 'Withdraw from'),
                items: eligibleBuckets
                    .map(
                      (bucket) => DropdownMenuItem(
                        value: bucket.id,
                        child: Text(
                          '${bucket.name} · ${data.currency} '
                          '${formatMoney(bucket.balance)}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _selectedBucketId = value);
                  }
                },
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: InputDecoration(
                  labelText: 'Amount',
                  prefixText: '${data.currency} ',
                  helperText:
                      'Available: ${data.currency} ${formatMoney(selectedBucket.balance)}',
                ),
              ),
              const SizedBox(height: 20),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                    value: 'MOBILE_MONEY',
                    label: Text('Mobile Money'),
                    icon: Icon(Icons.phone_android),
                  ),
                  ButtonSegment(
                    value: 'BANK',
                    label: Text('Bank'),
                    icon: Icon(Icons.account_balance),
                  ),
                ],
                selected: {_method},
                onSelectionChanged: (selection) {
                  setState(() => _method = selection.first);
                },
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _nameController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Beneficiary name',
                ),
              ),
              const SizedBox(height: 14),
              if (_method == 'MOBILE_MONEY') ...[
                DropdownButtonFormField<String>(
                  initialValue: _network,
                  decoration: const InputDecoration(
                    labelText: 'Mobile money network',
                  ),
                  items: const [
                    DropdownMenuItem(value: 'MTN', child: Text('MTN')),
                    DropdownMenuItem(value: 'MPS', child: Text('MPS')),
                  ],
                  onChanged: (value) {
                    if (value != null) setState(() => _network = value);
                  },
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Mobile money number',
                  ),
                ),
              ],
              if (_method == 'BANK') ...[
                TextField(
                  controller: _bankCodeController,
                  decoration: const InputDecoration(labelText: 'Bank code'),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _branchCodeController,
                  decoration: const InputDecoration(labelText: 'Branch code'),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _accountController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Account number',
                  ),
                ),
              ],
              const SizedBox(height: 26),
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: _submitting ? null : () => _submit(selectedBucket),
                  child: _submitting
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Withdraw money'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _submit(SavingsBucketSummary bucket) async {
    final amount = int.tryParse(
      _amountController.text.replaceAll(',', '').trim(),
    );
    if (amount == null || amount <= 0) {
      _showError('Enter a valid amount.');
      return;
    }
    if (amount > bucket.balance) {
      _showError("The amount exceeds this bucket's available balance.");
      return;
    }
    if (_nameController.text.trim().isEmpty) {
      _showError('Enter the beneficiary name.');
      return;
    }
    if (_method == 'MOBILE_MONEY' && _phoneController.text.trim().isEmpty) {
      _showError('Enter the mobile money number.');
      return;
    }
    if (_method == 'BANK' &&
        (_bankCodeController.text.trim().isEmpty ||
            _branchCodeController.text.trim().isEmpty ||
            _accountController.text.trim().isEmpty)) {
      _showError('Complete the bank details.');
      return;
    }

    setState(() => _submitting = true);
    try {
      final response = await PaymentService.createWithdrawal(
        sourceType: 'SAVINGS',
        sourceId: bucket.id,
        amount: amount,
        method: _method,
        beneficiaryName: _nameController.text.trim(),
        network: _method == 'MOBILE_MONEY' ? _network : null,
        phoneNumber: _method == 'MOBILE_MONEY'
            ? _phoneController.text.trim()
            : null,
        bankCode: _method == 'BANK' ? _bankCodeController.text.trim() : null,
        branchCode: _method == 'BANK'
            ? _branchCodeController.text.trim()
            : null,
        accountNumber: _method == 'BANK'
            ? _accountController.text.trim()
            : null,
      );

      if (response['success'] != true) {
        throw PaymentServiceException(
          response['detail']?.toString() ??
              'Withdrawal could not be submitted.',
        );
      }

      ref.invalidate(dashboardProvider);
      if (mounted) {
        final messenger = ScaffoldMessenger.of(context);
        context.pop();
        messenger.showSnackBar(
          SnackBar(
            content: Text(
              response['message']?.toString() ?? 'Withdrawal submitted.',
            ),
          ),
        );
      }
    } catch (error) {
      _showError(error.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }
}
