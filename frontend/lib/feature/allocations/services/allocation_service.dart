import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../models/allocation_setup_status.dart';

class AllocationService {
  AllocationService._();

  static Future<AllocationSetupStatus> getSetupStatus() async {
    try {
      final response = await ApiClient.dio.get('/allocations/status/');

      final responseData = Map<String, dynamic>.from(response.data as Map);

      final data = Map<String, dynamic>.from(responseData['data'] as Map);

      return AllocationSetupStatus.fromJson(data);
    } on DioException catch (error) {
      throw _convertError(error);
    }
  }

  static Future<void> setupAllocation({
    required int spendAmount,
    required int saveAmount,
    required int growAmount,
    required int weeklyAmount,
    required int numberOfWeeks,
    required DateTime startDate,
    required int releaseWeekday,
    required String releaseTime,
    required int goalLockAmount,
    required int goalLockTargetAmount,
    required DateTime? goalLockTargetDate,
    required int emergencySaveAmount,
  }) async {
    try {
      await ApiClient.dio.post(
        '/allocations/setup/',
        data: {
          'spend_amount': spendAmount.toString(),
          'save_amount': saveAmount.toString(),
          'grow_amount': growAmount.toString(),
          'weekly_amount': weeklyAmount.toString(),
          'number_of_weeks': numberOfWeeks,
          'start_date': _formatDate(startDate),
          'release_weekday': releaseWeekday,
          'release_time': releaseTime,
          'goal_lock_amount': goalLockAmount.toString(),
          'goal_lock_target_amount': goalLockTargetAmount.toString(),
          'goal_lock_target_date': goalLockTargetDate == null
              ? null
              : _formatDate(goalLockTargetDate),
          'emergency_save_amount': emergencySaveAmount.toString(),
        },
      );
    } on DioException catch (error) {
      throw _convertError(error);
    }
  }

  static String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');

    return '${date.year}-$month-$day';
  }

  static String _convertError(DioException error) {
    final responseData = error.response?.data;

    if (responseData is Map) {
      final data = Map<String, dynamic>.from(responseData);

      if (data['error'] is Map) {
        final errorMap = Map<String, dynamic>.from(data['error']);

        for (final value in errorMap.values) {
          if (value is List && value.isNotEmpty) {
            return value.first.toString();
          }

          if (value != null) {
            return value.toString();
          }
        }
      }

      if (data['detail'] != null) {
        return data['detail'].toString();
      }
    }

    if (error.type == DioExceptionType.connectionTimeout) {
      return 'Connection timed out.';
    }

    if (error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to MasterSave.';
    }

    return 'Something went wrong. Please try again.';
  }
}
