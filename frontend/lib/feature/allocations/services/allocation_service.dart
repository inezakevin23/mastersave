import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../models/allocation_setup_status.dart';


class AllocationService {
  AllocationService._();

  static Future<
      AllocationSetupStatus>
      getSetupStatus() async {
    try {
      final response =
          await ApiClient.dio.get(
        '/allocations/status/',
      );

      final responseData =
          Map<String, dynamic>.from(
        response.data as Map,
      );

      final data =
          Map<String, dynamic>.from(
        responseData['data'] as Map,
      );

      return AllocationSetupStatus
          .fromJson(data);
    } on DioException catch (error) {
      throw _convertError(error);
    }
  }

  static String _convertError(
    DioException error,
  ) {
    if (error.response?.data
        is Map<String, dynamic>) {
      final data =
          Map<String, dynamic>.from(
        error.response!.data as Map,
      );

      if (data['detail'] != null) {
        return data['detail'].toString();
      }

      if (data['error'] != null) {
        return data['error'].toString();
      }
    }

    if (error.type ==
        DioExceptionType.connectionTimeout) {
      return 'Connection timed out.';
    }

    if (error.type ==
        DioExceptionType.connectionError) {
      return 'Unable to connect to MasterSave.';
    }

    return 'Unable to check your setup status.';
  }
}