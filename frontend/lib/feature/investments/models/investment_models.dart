import '../../dashboard/models/dashboard_models.dart';

class InvestmentProductModel {
  final String id;
  final String name;
  final String partnerName;
  final String description;
  final String currency;
  final int minimumAmount;
  final double annualRate;
  final int termMonths;
  final String riskLevel;
  final String riskInformation;

  const InvestmentProductModel({
    required this.id,
    required this.name,
    required this.partnerName,
    required this.description,
    required this.currency,
    required this.minimumAmount,
    required this.annualRate,
    required this.termMonths,
    required this.riskLevel,
    required this.riskInformation,
  });

  factory InvestmentProductModel.fromJson(Map<String, dynamic> json) {
    return InvestmentProductModel(
      id: json['id'].toString(),
      name: json['name']?.toString() ?? '',
      partnerName: json['partner_name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      currency: json['currency']?.toString() ?? 'RWF',
      minimumAmount: parseMoney(json['minimum_amount']),
      annualRate: parseDouble(json['annual_rate']),
      termMonths: parseMoney(json['term_months']),
      riskLevel: json['risk_level']?.toString() ?? 'UNKNOWN',
      riskInformation: json['risk_information']?.toString() ?? '',
    );
  }
}

class InvestmentRequestModel {
  final String id;
  final String productId;
  final String productName;
  final String reference;
  final int amount;
  final String status;
  final String rejectionReason;
  final DateTime? requestedAt;

  const InvestmentRequestModel({
    required this.id,
    required this.productId,
    required this.productName,
    required this.reference,
    required this.amount,
    required this.status,
    required this.rejectionReason,
    required this.requestedAt,
  });

  factory InvestmentRequestModel.fromJson(Map<String, dynamic> json) {
    final product = json['product'];
    return InvestmentRequestModel(
      id: json['id'].toString(),
      productId: product is Map ? product['id'].toString() : product.toString(),
      productName: json['product_name']?.toString() ??
          (product is Map ? product['name']?.toString() ?? '' : ''),
      reference: json['reference']?.toString() ?? '',
      amount: parseMoney(json['amount']),
      status: json['status']?.toString() ?? 'PENDING',
      rejectionReason: json['rejection_reason']?.toString() ?? '',
      requestedAt: DateTime.tryParse(json['requested_at']?.toString() ?? '')
          ?.toLocal(),
    );
  }
}

class InvestmentTransactionModel {
  final String id;
  final String productName;
  final String type;
  final String description;
  final String reference;
  final String status;
  final int amount;
  final DateTime? occurredAt;

  const InvestmentTransactionModel({
    required this.id,
    required this.productName,
    required this.type,
    required this.description,
    required this.reference,
    required this.status,
    required this.amount,
    required this.occurredAt,
  });

  factory InvestmentTransactionModel.fromJson(Map<String, dynamic> json) {
    return InvestmentTransactionModel(
      id: json['id'].toString(),
      productName: json['product_name']?.toString() ?? '',
      type: json['transaction_type']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      reference: json['reference']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      amount: parseMoney(json['amount']),
      occurredAt: DateTime.tryParse(json['occurred_at']?.toString() ?? '')
          ?.toLocal(),
    );
  }
}
