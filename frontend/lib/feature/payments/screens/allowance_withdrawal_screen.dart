import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../dashboard/models/dashboard_models.dart';
import '../../dashboard/providers/dashboard_provider.dart';
import '../services/payment_service.dart';

class AllowanceWithdrawalScreen extends ConsumerStatefulWidget {
  const AllowanceWithdrawalScreen({
    required this.releaseId,
    super.key,
  });

  final String releaseId;

  @override
  ConsumerState<AllowanceWithdrawalScreen> createState() =>
      _AllowanceWithdrawalScreenState();
}

class _AllowanceWithdrawalScreenState
    extends ConsumerState<AllowanceWithdrawalScreen> {
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bankCodeController = TextEditingController();
  final _branchCodeController = TextEditingController();
  final _accountController = TextEditingController();

  String _method = 'MOBILE_MONEY';
  String _network = 'MTN';
  bool _submitting = false;

  @override
  void dispose() {
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
      appBar: AppBar(title: const Text('Withdraw weekly allowance')),
      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
        data: (data) {
          final release = data.spend.withdrawalRelease;
          if (release == null || release.id != widget.releaseId) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'This allowance is no longer available to withdraw.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(
                'Week ${release.weekNumber}',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'RWF ${formatMoney(release.amount)}',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 24),
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
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  decoration: const InputDecoration(
                    labelText: 'Account number',
                  ),
                ),
              ],
              const SizedBox(height: 24),
              SizedBox(
                height: 54,
                child: ElevatedButton(
                  onPressed: _submitting ? null : () => _submit(release.id),
                  child: _submitting
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Submit payout'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _submit(String releaseId) async {
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
      final response = await PaymentService.createAllowanceWithdrawal(
        releaseId: releaseId,
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
          response['detail']?.toString() ?? 'Payout could not be submitted.',
        );
      }

      ref.invalidate(dashboardProvider);
      if (mounted) {
        final messenger = ScaffoldMessenger.of(context);
        context.pop();
        messenger.showSnackBar(
          const SnackBar(
            content: Text('Payout submitted; waiting for provider confirmation.'),
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
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}