import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../auth/providers/auth_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),

      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFEDEDED)),
            ),
            child: Column(
              children: [
                CircleAvatar(
                  radius: 34,
                  backgroundColor: const Color(0xFFDC2626),
                  child: Text(
                    _initials(user?.firstName, user?.lastName),
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                Text(
                  user?.fullName ?? 'Scholar',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                  ),
                ),

                const SizedBox(height: 4),

                Text(
                  user?.email ?? '',
                  style: const TextStyle(color: Color(0xFF697586)),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          ListTile(
            leading: const Icon(Icons.account_balance_wallet_outlined),
            title: const Text('View allocation'),
            subtitle: const Text('See how your allowance is divided'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              context.go('/allocation');
            },
          ),

          const Divider(),

          ListTile(
            leading: const Icon(Icons.logout, color: Color(0xFFDC2626)),
            title: const Text('Log out'),
            onTap: () async {
              await ref.read(authProvider.notifier).logout();
            },
          ),
        ],
      ),
    );
  }

  String _initials(String? first, String? last) {
    final firstInitial = first != null && first.isNotEmpty ? first[0] : '';

    final lastInitial = last != null && last.isNotEmpty ? last[0] : '';

    return '$firstInitial$lastInitial'.toUpperCase();
  }
}
