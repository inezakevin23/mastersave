import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/allocation_setup_status.dart';
import '../services/allocation_service.dart';

final allocationSetupStatusProvider = FutureProvider<AllocationSetupStatus>(
  (ref) => AllocationService.getSetupStatus(),
);
