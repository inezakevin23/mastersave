import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../models/dashboard_models.dart';

class DashboardService {
  DashboardService._();

  static Future<DashboardData> getDashboard() async {
    try {
      final response = await ApiClient.dio.get('/dashboard/');

      final data = Map<String, dynamic>.from(response.data as Map);

      if (data['data'] == null) {
        throw Exception('Dashboard data was not returned.');
      }

      return DashboardData.fromJson(
        Map<String, dynamic>.from(data['data'] as Map),
      );
    } on DioException catch (error) {
      throw _convertError(error);
    }
  }

  static String _convertError(DioException error) {
    if (error.response?.data is Map<String, dynamic>) {
      final data = Map<String, dynamic>.from(error.response!.data as Map);

      if (data['detail'] != null) {
        return data['detail'].toString();
      }

      if (data['error'] != null) {
        return data['error'].toString();
      }
    }

    if (error.type == DioExceptionType.connectionTimeout) {
      return 'Connection timed out.';
    }

    if (error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to MasterSave.';
    }

    return 'Unable to load your dashboard.';
  }
}
