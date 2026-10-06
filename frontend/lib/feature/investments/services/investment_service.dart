import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../models/investment_models.dart';

class InvestmentService {
  InvestmentService._();

  static Future<List<InvestmentProductModel>> getProducts() async {
    try {
      final response = await ApiClient.dio.get('/investments/products/');
      final rows = _asList(response.data);
      return rows
          .map(
            (row) => InvestmentProductModel.fromJson(
              Map<String, dynamic>.from(row as Map),
            ),
          )
          .toList();
    } on DioException catch (error) {
      throw InvestmentServiceException(_message(error));
    }
  }

  static Future<List<InvestmentRequestModel>> getRequests() async {
    try {
      final response = await ApiClient.dio.get('/investments/requests/');
      final rows = _asList(response.data);
      return rows
          .map(
            (row) => InvestmentRequestModel.fromJson(
              Map<String, dynamic>.from(row as Map),
            ),
          )
          .toList();
    } on DioException catch (error) {
      throw InvestmentServiceException(_message(error));
    }
  }

  static Future<List<InvestmentTransactionModel>> getTransactions() async {
    try {
      final response = await ApiClient.dio.get('/investments/transactions/');
      final rows = _asList(response.data);
      return rows
          .map(
            (row) => InvestmentTransactionModel.fromJson(
              Map<String, dynamic>.from(row as Map),
            ),
          )
          .toList();
    } on DioException catch (error) {
      throw InvestmentServiceException(_message(error));
    }
  }

  static Future<void> submitRequest({
    required String allocationId,
    required String productId,
    required int amount,
  }) async {
    try {
      await ApiClient.dio.post(
        '/investments/requests/',
        data: {
          'source_allocation': allocationId,
          'product': productId,
          'amount': amount,
        },
      );
    } on DioException catch (error) {
      throw InvestmentServiceException(_message(error));
    }
  }

  static List<dynamic> _asList(dynamic data) {
    if (data is List) return data;
    if (data is Map && data['results'] is List) {
      return data['results'] as List;
    }
    throw const InvestmentServiceException(
      'The server returned an invalid investment response.',
    );
  }

  static String _message(DioException error) {
    final data = error.response?.data;
    if (data is Map) {
      final detail = data['detail'] ?? data['error'];
      if (detail != null) return detail.toString();
      for (final value in data.values) {
        if (value is List && value.isNotEmpty) return value.first.toString();
      }
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to MasterSave.';
    }
    return 'Unable to load investment information.';
  }
}

class InvestmentServiceException implements Exception {
  final String message;

  const InvestmentServiceException(this.message);

  @override
  String toString() => message;
}
