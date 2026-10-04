import 'package:intl/intl.dart';

int parseMoney(dynamic value) {
  if (value == null) {
    return 0;
  }

  if (value is int) {
    return value;
  }

  if (value is double) {
    return value.round();
  }

  return int.tryParse(value.toString()) ?? 0;
}

double parseDouble(dynamic value) {
  if (value == null) {
    return 0;
  }

  if (value is num) {
    return value.toDouble();
  }

  return double.tryParse(value.toString()) ?? 0;
}

String formatMoney(int amount) {
  return NumberFormat('#,##0').format(amount);
}

String formatPercent(double value) {
  return NumberFormat('0.##').format(value);
}

class DashboardData {
  final int totalDeposited;
  final int totalAllocated;
  final int unallocated;
  final String currency;
  final SpendSummary spend;
  final SaveSummary save;
  final GrowSummary grow;

  const DashboardData({
    required this.totalDeposited,
    required this.totalAllocated,
    required this.unallocated,
    required this.currency,
    required this.spend,
    required this.save,
    required this.grow,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      totalDeposited: parseMoney(json['total_deposited']),
      totalAllocated: parseMoney(json['total_allocated']),
      unallocated: parseMoney(json['unallocated']),
      currency: json['currency'] as String? ?? 'RWF',
      spend: SpendSummary.fromJson(
        Map<String, dynamic>.from(json['spend'] as Map),
      ),
      save: SaveSummary.fromJson(
        Map<String, dynamic>.from(json['save'] as Map),
      ),
      grow: GrowSummary.fromJson(
        Map<String, dynamic>.from(json['grow'] as Map),
      ),
    );
  }
}

class SpendSummary {
  final int allocated;
  final int? currentWeek;
  final int? totalWeeks;
  final int? weeklyBudget;
  final int usedThisWeek;
  final int? remainingThisWeek;
  final DateTime? nextRelease;

  const SpendSummary({
    required this.allocated,
    required this.currentWeek,
    required this.totalWeeks,
    required this.weeklyBudget,
    required this.usedThisWeek,
    required this.remainingThisWeek,
    required this.nextRelease,
  });

  factory SpendSummary.fromJson(Map<String, dynamic> json) {
    final rawNextRelease = json['next_release'];

    return SpendSummary(
      allocated: parseMoney(json['allocated']),
      currentWeek: json['current_week'] as int?,
      totalWeeks: json['total_weeks'] as int?,
      weeklyBudget: json['weekly_budget'] == null
          ? null
          : parseMoney(json['weekly_budget']),
      usedThisWeek: parseMoney(json['used_this_week']),
      remainingThisWeek: json['remaining_this_week'] == null
          ? null
          : parseMoney(json['remaining_this_week']),
      nextRelease: rawNextRelease == null
          ? null
          : DateTime.tryParse(rawNextRelease.toString())?.toLocal(),
    );
  }
}

class SaveSummary {
  final int allocated;
  final int totalSaved;
  final int unassigned;
  final List<SavingsBucketSummary> buckets;

  const SaveSummary({
    required this.allocated,
    required this.totalSaved,
    required this.unassigned,
    required this.buckets,
  });

  factory SaveSummary.fromJson(Map<String, dynamic> json) {
    final rawBuckets = json['buckets'] as List? ?? [];

    return SaveSummary(
      allocated: parseMoney(json['allocated']),
      totalSaved: parseMoney(json['total_saved']),
      unassigned: parseMoney(json['unassigned']),
      buckets: rawBuckets
          .map(
            (bucket) => SavingsBucketSummary.fromJson(
              Map<String, dynamic>.from(bucket as Map),
            ),
          )
          .toList(),
    );
  }
}

class SavingsBucketSummary {
  final String id;
  final String name;
  final String type;
  final int balance;
  final int? targetAmount;
  final int? remainingToTarget;
  final double? progressPercentage;
  final bool isLocked;
  final String status;

  const SavingsBucketSummary({
    required this.id,
    required this.name,
    required this.type,
    required this.balance,
    required this.targetAmount,
    required this.remainingToTarget,
    required this.progressPercentage,
    required this.isLocked,
    required this.status,
  });

  factory SavingsBucketSummary.fromJson(Map<String, dynamic> json) {
    return SavingsBucketSummary(
      id: json['id'].toString(),
      name: json['name'] as String,
      type: json['type'] as String,
      balance: parseMoney(json['balance']),
      targetAmount: json['target_amount'] == null
          ? null
          : parseMoney(json['target_amount']),
      remainingToTarget: json['remaining_to_target'] == null
          ? null
          : parseMoney(json['remaining_to_target']),
      progressPercentage: json['progress_percentage'] == null
          ? null
          : parseDouble(json['progress_percentage']),
      isLocked: json['is_locked'] == true,
      status: json['status'] as String,
    );
  }
}

class GrowSummary {
  final int allocated;
  final int reserved;
  final int invested;
  final int available;
  final int investmentBalance;
  final int projectedReturn;
  final List<InvestmentAccountSummary> accounts;

  const GrowSummary({
    required this.allocated,
    required this.reserved,
    required this.invested,
    required this.available,
    required this.investmentBalance,
    required this.projectedReturn,
    required this.accounts,
  });

  factory GrowSummary.fromJson(Map<String, dynamic> json) {
    final rawAccounts = json['accounts'] as List? ?? [];

    return GrowSummary(
      allocated: parseMoney(json['allocated']),
      reserved: parseMoney(json['reserved']),
      invested: parseMoney(json['invested']),
      available: parseMoney(json['available']),
      investmentBalance: parseMoney(json['investment_balance']),
      projectedReturn: parseMoney(json['projected_return']),
      accounts: rawAccounts
          .map(
            (account) => InvestmentAccountSummary.fromJson(
              Map<String, dynamic>.from(account as Map),
            ),
          )
          .toList(),
    );
  }
}

class InvestmentAccountSummary {
  final String id;
  final String productName;
  final String partnerName;
  final int principal;
  final int balance;
  final double annualRate;
  final int termMonths;
  final int projectedReturn;
  final String status;
  final DateTime? maturityDate;

  const InvestmentAccountSummary({
    required this.id,
    required this.productName,
    required this.partnerName,
    required this.principal,
    required this.balance,
    required this.annualRate,
    required this.termMonths,
    required this.projectedReturn,
    required this.status,
    required this.maturityDate,
  });

  factory InvestmentAccountSummary.fromJson(Map<String, dynamic> json) {
    return InvestmentAccountSummary(
      id: json['id'].toString(),
      productName: json['product_name'] as String,
      partnerName: json['partner_name'] as String,
      principal: parseMoney(json['principal']),
      balance: parseMoney(json['balance']),
      annualRate: parseDouble(json['annual_rate']),
      termMonths: json['term_months'] as int,
      projectedReturn: parseMoney(json['projected_return']),
      status: json['status'] as String,
      maturityDate: json['maturity_date'] == null
          ? null
          : DateTime.tryParse(json['maturity_date'].toString()),
    );
  }
}
