class AllocationSectionStatus {
  final int allocated;
  final bool configured;

  const AllocationSectionStatus({
    required this.allocated,
    required this.configured,
  });

  factory AllocationSectionStatus.fromJson(
    Map<String, dynamic> json,
  ) {
    final rawAmount = json['allocated'];

    int amount = 0;

    if (rawAmount is num) {
      amount = rawAmount.toInt();
    } else {
      amount = int.tryParse(
            rawAmount?.toString() ?? '0',
          ) ??
          0;
    }

    return AllocationSectionStatus(
      allocated: amount,
      configured:
          json['configured'] == true,
    );
  }
}


class AllocationSetupStatus {
  final bool setupComplete;
  final bool hasSuccessfulDeposit;
  final bool hasUnallocatedDeposit;
  final String? latestDepositId;
  final String? allocationId;

  final AllocationSectionStatus spend;
  final AllocationSectionStatus save;
  final AllocationSectionStatus grow;

  const AllocationSetupStatus({
    required this.setupComplete,
    required this.hasSuccessfulDeposit,
    required this.hasUnallocatedDeposit,
    required this.latestDepositId,
    required this.allocationId,
    required this.spend,
    required this.save,
    required this.grow,
  });

  factory AllocationSetupStatus.fromJson(
    Map<String, dynamic> json,
  ) {
    return AllocationSetupStatus(
      setupComplete:
          json['setup_complete'] == true,

      hasSuccessfulDeposit:
          json['has_successful_deposit'] == true,

      hasUnallocatedDeposit:
          json['has_unallocated_deposit'] ==
              true,

      latestDepositId:
          json['latest_deposit_id']
              ?.toString(),

      allocationId:
          json['allocation_id']
              ?.toString(),

      spend:
          AllocationSectionStatus.fromJson(
        Map<String, dynamic>.from(
          json['spend'] as Map,
        ),
      ),

      save:
          AllocationSectionStatus.fromJson(
        Map<String, dynamic>.from(
          json['save'] as Map,
        ),
      ),

      grow:
          AllocationSectionStatus.fromJson(
        Map<String, dynamic>.from(
          json['grow'] as Map,
        ),
      ),
    );
  }
}