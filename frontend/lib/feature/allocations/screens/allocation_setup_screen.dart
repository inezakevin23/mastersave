import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:frontend/feature/dashboard/providers/dashboard_provider.dart';

import '../models/allocation_setup_status.dart';
import '../providers/allocation_provider.dart';
import '../services/allocation_service.dart';

class AllocationSetupScreen extends ConsumerStatefulWidget {
  const AllocationSetupScreen({super.key});

  @override
  ConsumerState<AllocationSetupScreen> createState() =>
      _AllocationSetupScreenState();
}

class _AllocationSetupScreenState extends ConsumerState<AllocationSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _spendController = TextEditingController();
  final _saveController = TextEditingController();
  final _growController = TextEditingController();
  final _weeklyController = TextEditingController();
  final _weeksController = TextEditingController(text: '12');
  final _goalController = TextEditingController();
  final _goalTargetController = TextEditingController();
  final _emergencyController = TextEditingController();

  bool _submitting = false;

  @override
  void initState() {
    super.initState();

    for (final controller in [
      _spendController,
      _saveController,
      _growController,
      _weeklyController,
      _weeksController,
      _goalController,
      _goalTargetController,
      _emergencyController,
    ]) {
      controller.addListener(_rebuild);
    }
  }

  @override
  void dispose() {
    _spendController.dispose();
    _saveController.dispose();
    _growController.dispose();
    _weeklyController.dispose();
    _weeksController.dispose();
    _goalController.dispose();
    _goalTargetController.dispose();
    _emergencyController.dispose();
    super.dispose();
  }

  void _rebuild() {
    if (mounted) {
      setState(() {});
    }
  }

  int _money(TextEditingController controller) {
    return int.tryParse(controller.text.replaceAll(',', '').trim()) ?? 0;
  }

  int get spend => _money(_spendController);
  int get save => _money(_saveController);
  int get grow => _money(_growController);
  int get weekly => _money(_weeklyController);
  int get weeks => int.tryParse(_weeksController.text.trim()) ?? 0;
  int get goal => _money(_goalController);
  int get goalTarget => _money(_goalTargetController);
  int get emergency => _money(_emergencyController);
  int get allocated => spend + save + grow;
  int get saveSplit => goal + emergency;

  @override
  Widget build(BuildContext context) {
    final setup = ref.watch(allocationSetupStatusProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(title: const Text('Set up your allowance')),
      body: setup.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
        data: (status) => _buildForm(context, status),
      ),
    );
  }

  Widget _buildForm(BuildContext context, AllocationSetupStatus status) {
    if (!status.hasUnallocatedDeposit) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'There is currently no unallocated allowance available.',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    final total = status.latestDepositAmount;
    final remaining = total - allocated;
    final allocationValid = allocated == total;
    final saveValid = save == saveSplit;
    final weeklyValid = weeks > 0 && weekly * weeks == spend;
    final goalTargetValid = goalTarget > 0 && goalTarget >= goal;

    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 10, 20, 32),
        children: [
          _AmountHeader(
            total: total,
            allocated: allocated,
            remaining: remaining,
          ),
          const SizedBox(height: 18),
          _SectionCard(
            title: '1. Split your allowance',
            subtitle: 'Decide how much goes to Spend, Save, and Grow.',
            child: Column(
              children: [
                _MoneyField(controller: _spendController, label: 'Spend'),
                const SizedBox(height: 12),
                _MoneyField(controller: _saveController, label: 'Save'),
                const SizedBox(height: 12),
                _MoneyField(controller: _growController, label: 'Grow'),
                const SizedBox(height: 16),
                _ValidationRow(
                  label: 'Allocation remaining',
                  amount: remaining,
                  valid: allocationValid,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _SectionCard(
            title: '2. Set your weekly Spend',
            subtitle: 'Your Spend amount will be released weekly.',
            child: Column(
              children: [
                _MoneyField(
                  controller: _weeklyController,
                  label: 'Weekly budget',
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _weeksController,
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  decoration: const InputDecoration(
                    labelText: 'Number of weeks',
                    suffixText: 'weeks',
                  ),
                  validator: (value) {
                    final parsed = int.tryParse(value ?? '');
                    if (parsed == null || parsed < 1 || parsed > 52) {
                      return 'Enter between 1 and 52 weeks.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                _ValidationMessage(
                  visible: weekly > 0 && weeks > 0 && !weeklyValid,
                  message: 'Weekly budget × number of weeks must equal your Spend amount.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _SectionCard(
            title: '3. Split your Save allocation',
            subtitle: 'Create your Goal Lock and Emergency Save.',
            child: Column(
              children: [
                _MoneyField(controller: _goalController, label: 'Goal Lock'),
                const SizedBox(height: 12),
                _MoneyField(
                  controller: _goalTargetController,
                  label: 'Goal target',
                ),
                const SizedBox(height: 12),
                _MoneyField(
                  controller: _emergencyController,
                  label: 'Emergency Save',
                ),
                const SizedBox(height: 16),
                _ValidationRow(
                  label: 'Save amount remaining',
                  amount: save - saveSplit,
                  valid: saveValid,
                ),
                const SizedBox(height: 8),
                _ValidationMessage(
                  visible:
                      _goalTargetController.text.isNotEmpty && !goalTargetValid,
                  message: 'Goal target must be greater than or equal to Goal Lock and above zero.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 54,
            child: ElevatedButton(
              onPressed:
                  _submitting ||
                      !allocationValid ||
                      !saveValid ||
                      !weeklyValid ||
                      !goalTargetValid
                  ? null
                  : () => _submit(total),
              child: _submitting
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text('Set up my allowance'),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submit(int total) async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _submitting = true;
    });

    final now = DateTime.now();
    final daysUntilMonday = (DateTime.monday - now.weekday + 7) % 7;
    final startDate = DateTime(
      now.year,
      now.month,
      now.day,
    ).add(Duration(days: daysUntilMonday));

    try {
      await AllocationService.setupAllocation(
        spendAmount: spend,
        saveAmount: save,
        growAmount: grow,
        weeklyAmount: weekly,
        numberOfWeeks: weeks,
        startDate: startDate,
        releaseWeekday: 0,
        releaseTime: '09:00:00',
        goalLockAmount: goal,
        goalLockTargetAmount: goalTarget,
        goalLockTargetDate: null,
        emergencySaveAmount: emergency,
      );

      ref.invalidate(allocationSetupStatusProvider);
      ref.invalidate(dashboardProvider);

      if (mounted) {
        context.go('/');
      }
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) {
        setState(() {
          _submitting = false;
        });
      }
    }
  }
}

class _AmountHeader extends StatelessWidget {
  final int total;
  final int allocated;
  final int remaining;

  const _AmountHeader({
    required this.total,
    required this.allocated,
    required this.remaining,
  });

  @override
  Widget build(BuildContext context) {
    final isComplete = remaining == 0;

    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE8E8E8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'AVAILABLE ALLOWANCE',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: Color(0xFF8490A0),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'RWF ${formatMoney(total)}',
            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 18),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Allocated: RWF ${formatMoney(allocated)}',
                style: const TextStyle(fontSize: 12, color: Color(0xFF536070)),
              ),
              Text(
                remaining >= 0
                    ? 'Remaining: RWF ${formatMoney(remaining)}'
                    : 'Over by: RWF ${formatMoney(remaining.abs())}',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: isComplete
                      ? const Color(0xFF059669)
                      : remaining < 0
                      ? const Color(0xFFDC2626)
                      : const Color(0xFF536070),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: total == 0 ? 0 : (allocated / total).clamp(0.0, 1.0),
              minHeight: 7,
              backgroundColor: const Color(0xFFE5E7EB),
              color: isComplete
                  ? const Color(0xFF059669)
                  : const Color(0xFFDC2626),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final Widget child;

  const _SectionCard({
    required this.title,
    required this.subtitle,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFEFEFEF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 5),
          Text(
            subtitle,
            style: const TextStyle(fontSize: 12, color: Color(0xFF697586)),
          ),
          const SizedBox(height: 18),
          child,
        ],
      ),
    );
  }
}

class _MoneyField extends StatelessWidget {
  final TextEditingController controller;
  final String label;

  const _MoneyField({required this.controller, required this.label});

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.number,
      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
      decoration: InputDecoration(labelText: label, prefixText: 'RWF '),
      validator: (value) {
        if (value == null || value.trim().isEmpty) {
          return '$label is required.';
        }

        return null;
      },
    );
  }
}

class _ValidationRow extends StatelessWidget {
  final String label;
  final int amount;
  final bool valid;

  const _ValidationRow({
    required this.label,
    required this.amount,
    required this.valid,
  });

  @override
  Widget build(BuildContext context) {
    final color = valid ? const Color(0xFF059669) : const Color(0xFFDC2626);

    return Row(
      children: [
        Icon(
          valid ? Icons.check_circle : Icons.error_outline,
          size: 18,
          color: color,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            '$label: RWF ${formatMoney(amount.abs())}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ),
      ],
    );
  }
}

class _ValidationMessage extends StatelessWidget {
  final bool visible;
  final String message;

  const _ValidationMessage({required this.visible, required this.message});

  @override
  Widget build(BuildContext context) {
    if (!visible) {
      return const SizedBox.shrink();
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.error_outline, size: 18, color: Color(0xFFDC2626)),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            message,
            style: const TextStyle(fontSize: 12, color: Color(0xFFDC2626)),
          ),
        ),
      ],
    );
  }
}

String formatMoney(int amount) {
  final digits = amount.toString();
  final buffer = StringBuffer();

  for (var index = 0; index < digits.length; index++) {
    buffer.write(digits[index]);
    final remainingDigits = digits.length - index - 1;
    if (remainingDigits > 0 && remainingDigits % 3 == 0) {
      buffer.write(',');
    }
  }

  return buffer.toString();
}
