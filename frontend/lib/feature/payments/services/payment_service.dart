import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';

class PaymentServiceException implements Exception {
  const PaymentServiceException(this.message);

  final String message;

  @override
  String toString() => message;
}

class PaymentService {
  PaymentService._();

  static Future<Map<String, dynamic>> createWithdrawal({
    required String sourceType,
    required String sourceId,
    required int amount,
    required String method,
    required String beneficiaryName,
    String? network,
    String? phoneNumber,
    String? bankCode,
    String? branchCode,
    String? accountNumber,
  }) {
    return _postWithdrawal({
      'source_type': sourceType,
      'source_id': sourceId,
      'amount': amount.toString(),
      'destination': _destinationPayload(
        method: method,
        beneficiaryName: beneficiaryName,
        network: network,
        phoneNumber: phoneNumber,
        bankCode: bankCode,
        branchCode: branchCode,
        accountNumber: accountNumber,
      ),
    });
  }

  static Future<Map<String, dynamic>> createAllowanceWithdrawal({
    required String releaseId,
    required String method,
    required String beneficiaryName,
    String? network,
    String? phoneNumber,
    String? bankCode,
    String? branchCode,
    String? accountNumber,
  }) {
    return _postWithdrawal({
      'source_type': 'ALLOWANCE',
      'source_id': releaseId,
      'destination': _destinationPayload(
        method: method,
        beneficiaryName: beneficiaryName,
        network: network,
        phoneNumber: phoneNumber,
        bankCode: bankCode,
        branchCode: branchCode,
        accountNumber: accountNumber,
      ),
    });
  }

  static Map<String, dynamic> _destinationPayload({
    required String method,
    required String beneficiaryName,
    String? network,
    String? phoneNumber,
    String? bankCode,
    String? branchCode,
    String? accountNumber,
  }) {
    return {
      'method': method,
      'beneficiary_name': beneficiaryName,
      'network': network ?? '',
      'phone_number': phoneNumber ?? '',
      'bank_code': bankCode ?? '',
      'branch_code': branchCode ?? '',
      'account_number': accountNumber ?? '',
      'currency': 'RWF',
    };
  }

  static Future<Map<String, dynamic>> _postWithdrawal(
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await ApiClient.dio.post(
        '/payments/withdrawals/',
        data: data,
      );

      final responseData = response.data;
      if (responseData is! Map) {
        throw const PaymentServiceException(
          'The server returned an invalid withdrawal response.',
        );
      }
      return Map<String, dynamic>.from(responseData);
    } on DioException catch (error) {
      throw PaymentServiceException(_errorMessage(error));
    }
  }

  static String _errorMessage(DioException error) {
    final responseMessage = _extractError(error.response?.data);
    if (responseMessage != null && responseMessage.isNotEmpty) {
      return responseMessage;
    }

    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return 'The withdrawal request timed out. Check your payouts before trying again.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to MasterSave.';
    }
    return 'Unable to submit the withdrawal. Please try again.';
  }

  static String? _extractError(dynamic value) {
    if (value is String) {
      return value;
    }
    if (value is List) {
      for (final item in value) {
        final message = _extractError(item);
        if (message != null && message.isNotEmpty) return message;
      }
      return null;
    }
    if (value is Map) {
      for (final key in [
        'detail',
        'error',
        'amount',
        'source_id',
        'destination',
        'destination_id',
        'network',
        'phone_number',
        'bank_code',
        'branch_code',
        'account_number',
      ]) {
        if (value.containsKey(key)) {
          final message = _extractError(value[key]);
          if (message != null && message.isNotEmpty) return message;
        }
      }
      for (final entry in value.entries) {
        if (entry.key == 'success') continue;
        final message = _extractError(entry.value);
        if (message != null && message.isNotEmpty) {
          return '${entry.key}: $message';
        }
      }
    }
    return null;
  }
}
