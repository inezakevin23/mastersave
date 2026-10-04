import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/providers/auth_provider.dart';
import '../models/dashboard_models.dart';
import '../services/dashboard_service.dart';

class DashboardNotifier extends AsyncNotifier<DashboardData> {
  @override
  Future<DashboardData> build() async {
    final authState = ref.watch(authProvider);

    if (authState.status != AuthStatus.authenticated) {
      throw StateError('User is not authenticated.');
    }

    return DashboardService.getDashboard();
  }

  Future<void> refreshDashboard() async {
    state = await AsyncValue.guard(DashboardService.getDashboard);
  }
}

final dashboardProvider =
    AsyncNotifierProvider<DashboardNotifier, DashboardData>(
      DashboardNotifier.new,
    );
