import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../dashboard/models/dashboard_models.dart';
import '../../dashboard/providers/dashboard_provider.dart';

class AllocationOverviewScreen extends ConsumerWidget {
  const AllocationOverviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Your allocation')),

      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),

        error: (error, stackTrace) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),

        data: (data) => RefreshIndicator(
          onRefresh: () {
            return ref.read(dashboardProvider.notifier).refreshDashboard();
          },

          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
            children: [
              _TotalCard(data: data),

              const SizedBox(height: 18),

              _AllocationCard(
                title: 'Spend',
                amount: data.spend.allocated,
                icon: Icons.shopping_bag_outlined,
                description: 'Weekly allowance and everyday spending',
                onTap: () {
                  context.go('/spend');
                },
              ),

              const SizedBox(height: 12),

              _AllocationCard(
                title: 'Save',
                amount: data.save.allocated,
                icon: Icons.savings_outlined,
                description: 'Goal Lock and Emergency Save',
                onTap: () {
                  context.go('/save');
                },
              ),

              const SizedBox(height: 12),

              _AllocationCard(
                title: 'Grow',
                amount: data.grow.allocated,
                icon: Icons.trending_up,
                description: 'Investment allocation',
                onTap: () {
                  context.go('/grow');
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TotalCard extends StatelessWidget {
  final DashboardData data;

  const _TotalCard({required this.data});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),

      decoration: BoxDecoration(
        color: const Color(0xFFDC2626),
        borderRadius: BorderRadius.circular(22),
      ),

      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'TOTAL ALLOWANCE',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1,
            ),
          ),

          const SizedBox(height: 8),

          Text(
            'RWF ${formatMoney(data.totalDeposited)}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 34,
              fontWeight: FontWeight.w900,
            ),
          ),

          const SizedBox(height: 8),

          const Text(
            'Your allowance is divided across Spend, Save, and Grow.',
            style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _AllocationCard extends StatelessWidget {
  final String title;
  final int amount;
  final IconData icon;
  final String description;
  final VoidCallback onTap;

  const _AllocationCard({
    required this.title,
    required this.amount,
    required this.icon,
    required this.description,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),

      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,

        child: Container(
          padding: const EdgeInsets.all(18),

          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),

            border: Border.all(color: const Color(0xFFEDEDED)),
          ),

          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: const Color(0xFFFBEAEA),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: const Color(0xFFDC2626)),
              ),

              const SizedBox(width: 14),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),

                    const SizedBox(height: 4),

                    Text(
                      description,
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF697586),
                      ),
                    ),
                  ],
                ),
              ),

              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'RWF',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF98A1AD),
                    ),
                  ),

                  Text(
                    formatMoney(amount),
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w900,
                    ),
                  ),

                  const SizedBox(height: 2),

                  const Icon(
                    Icons.arrow_forward_ios,
                    size: 13,
                    color: Color(0xFF98A1AD),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
