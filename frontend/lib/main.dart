import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/network/api_client.dart';
import 'core/routing/app_router.dart';
import 'core/theme/app_theme.dart';
import 'feature/auth/providers/auth_provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  ApiClient.initialize();

  runApp(const ProviderScope(child: MasterSaveApp()));
}

class MasterSaveApp extends ConsumerStatefulWidget {
  const MasterSaveApp({super.key});

  @override
  ConsumerState<MasterSaveApp> createState() => _MasterSaveAppState();
}

class _MasterSaveAppState extends ConsumerState<MasterSaveApp> {
  late final GoRouter router;

  @override
  void initState() {
    super.initState();

    router = AppRouter.createRouter(ref);

    ApiClient.onSessionExpired = () async {
      await ref.read(authProvider.notifier).logout();
    };

    ref.listenManual(authProvider, (previous, next) {
      router.refresh();
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'MasterSave',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      routerConfig: router,
    );
  }
}
