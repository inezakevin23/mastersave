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

class AllowanceReleaseSummary {
  final String id;
  final String? planId;
  final int weekNumber;
  final int amount;
  final String? status;
  final DateTime? releasedAt;
  final DateTime? scheduledAt;

  const AllowanceReleaseSummary({
    required this.id,
    required this.planId,
    required this.weekNumber,
    required this.amount,
    required this.status,
    required this.releasedAt,
    required this.scheduledAt,
  });

  factory AllowanceReleaseSummary.fromJson(Map<String, dynamic> json) {
    return AllowanceReleaseSummary(
      id: json['id']?.toString() ?? '',
      planId: json['plan_id']?.toString(),
      weekNumber: parseMoney(json['week_number']),
      amount: parseMoney(json['amount']),
      status: json['status']?.toString(),
      releasedAt: json['released_at'] == null
          ? null
          : DateTime.tryParse(json['released_at'].toString())?.toLocal(),
      scheduledAt: json['scheduled_at'] == null
          ? null
          : DateTime.tryParse(json['scheduled_at'].toString())?.toLocal(),
    );
  }
}

class SpendSummary {
  final int allocated;
  final List<AllowancePlanSummary> plans;
  final int? currentWeek;
  final int? totalWeeks;
  final int? weeklyAmount;
  final AllowanceReleaseSummary? currentRelease;
  final AllowanceReleaseSummary? nextRelease;
  final DueAllowanceReleaseSummary? withdrawalRelease;
  final List<DueAllowanceReleaseSummary> withdrawalReleases;

  const SpendSummary({
    required this.allocated,
    required this.plans,
    required this.currentWeek,
    required this.totalWeeks,
    required this.weeklyAmount,
    required this.currentRelease,
    required this.nextRelease,
    required this.withdrawalRelease,
    required this.withdrawalReleases,
  });

  factory SpendSummary.fromJson(Map<String, dynamic> json) {
    final rawCurrentRelease = json['current_release'];
    final rawNextRelease = json['next_release'];
    final rawWithdrawalRelease = json['withdrawal_release'];
    final rawPlans = json['plans'] as List? ?? [];
    final rawWithdrawalReleases = json['withdrawal_releases'] as List? ?? [];

    return SpendSummary(
      allocated: parseMoney(json['allocated']),
      plans: rawPlans
          .map(
            (plan) => AllowancePlanSummary.fromJson(
              Map<String, dynamic>.from(plan as Map),
            ),
          )
          .toList(),
      currentWeek: json['current_week'] as int?,
      totalWeeks: json['total_weeks'] as int?,
      weeklyAmount: json['weekly_amount'] == null
          ? null
          : parseMoney(json['weekly_amount']),
      currentRelease: rawCurrentRelease is Map
          ? AllowanceReleaseSummary.fromJson(
              Map<String, dynamic>.from(rawCurrentRelease),
            )
          : null,
      nextRelease: rawNextRelease is Map
          ? AllowanceReleaseSummary.fromJson(
              Map<String, dynamic>.from(rawNextRelease),
            )
          : null,
      withdrawalRelease: rawWithdrawalRelease is Map
          ? DueAllowanceReleaseSummary.fromJson(
              Map<String, dynamic>.from(rawWithdrawalRelease),
            )
          : null,
      withdrawalReleases: rawWithdrawalReleases
          .map(
            (release) => DueAllowanceReleaseSummary.fromJson(
              Map<String, dynamic>.from(release as Map),
            ),
          )
          .toList(),
    );
  }
}

class AllowancePlanSummary {
  final String id;
  final int allocated;
  final int weeklyAmount;
  final int numberOfWeeks;
  final DateTime? startDate;
  final int? currentWeek;

  const AllowancePlanSummary({
    required this.id,
    required this.allocated,
    required this.weeklyAmount,
    required this.numberOfWeeks,
    required this.startDate,
    required this.currentWeek,
  });

  factory AllowancePlanSummary.fromJson(Map<String, dynamic> json) {
    return AllowancePlanSummary(
      id: json['id']?.toString() ?? '',
      allocated: parseMoney(json['allocated']),
      weeklyAmount: parseMoney(json['weekly_amount']),
      numberOfWeeks: parseMoney(json['number_of_weeks']),
      startDate: DateTime.tryParse(json['start_date']?.toString() ?? '')
          ?.toLocal(),
      currentWeek: json['current_week'] as int?,
    );
  }
}

class DueAllowanceReleaseSummary {
  final String id;
  final String? planId;
  final int weekNumber;
  final int amount;
  final DateTime? scheduledAt;

  const DueAllowanceReleaseSummary({
    required this.id,
    required this.planId,
    required this.weekNumber,
    required this.amount,
    required this.scheduledAt,
  });

  factory DueAllowanceReleaseSummary.fromJson(Map<String, dynamic> json) {
    return DueAllowanceReleaseSummary(
      id: json['id']?.toString() ?? '',
      planId: json['plan_id']?.toString(),
      weekNumber: parseMoney(json['week_number']),
      amount: parseMoney(json['amount']),
      scheduledAt: json['scheduled_at'] == null
          ? null
          : DateTime.tryParse(json['scheduled_at'].toString())?.toLocal(),
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
  final List<GrowAllocationSummary> allocations;
  final List<InvestmentAccountSummary> accounts;

  const GrowSummary({
    required this.allocated,
    required this.reserved,
    required this.invested,
    required this.available,
    required this.investmentBalance,
    required this.projectedReturn,
    required this.allocations,
    required this.accounts,
  });

  factory GrowSummary.fromJson(Map<String, dynamic> json) {
    final rawAccounts = json['accounts'] as List? ?? [];
    final rawAllocations = json['allocations'] as List? ?? [];

    return GrowSummary(
      allocated: parseMoney(json['allocated']),
      reserved: parseMoney(json['reserved']),
      invested: parseMoney(json['invested']),
      available: parseMoney(json['available']),
      investmentBalance: parseMoney(json['investment_balance']),
      projectedReturn: parseMoney(json['projected_return']),
      allocations: rawAllocations
          .map(
            (allocation) => GrowAllocationSummary.fromJson(
              Map<String, dynamic>.from(allocation as Map),
            ),
          )
          .toList(),
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

class GrowAllocationSummary {
  final String id;
  final int allocated;
  final int reserved;
  final int invested;
  final int available;

  const GrowAllocationSummary({
    required this.id,
    required this.allocated,
    required this.reserved,
    required this.invested,
    required this.available,
  });

  factory GrowAllocationSummary.fromJson(Map<String, dynamic> json) {
    return GrowAllocationSummary(
      id: json['allocation_id'].toString(),
      allocated: parseMoney(json['allocated']),
      reserved: parseMoney(json['reserved']),
      invested: parseMoney(json['invested']),
      available: parseMoney(json['available']),
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
