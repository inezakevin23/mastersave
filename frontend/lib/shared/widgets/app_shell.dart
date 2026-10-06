import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppShell extends StatelessWidget {
  final Widget child;

  const AppShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;

    final selectedIndex = _selectedIndex(location);

    return Scaffold(
      body: child,

      bottomNavigationBar: NavigationBar(
        selectedIndex: selectedIndex,

        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go('/');
              break;

            case 1:
              context.go('/allocation');
              break;

            case 2:
              context.go('/profile');
              break;
          }
        },

        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),

          NavigationDestination(
            icon: Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(Icons.account_balance_wallet),
            label: 'Allocation',
          ),

          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }

  int _selectedIndex(String location) {
    if (location.startsWith('/allocation')) {
      return 1;
    }

    if (location.startsWith('/spend') ||
        location.startsWith('/save') ||
        location.startsWith('/grow')) {
      return 1;
    }

    if (location.startsWith('/profile')) {
      return 2;
    }

    return 0;
  }
}
