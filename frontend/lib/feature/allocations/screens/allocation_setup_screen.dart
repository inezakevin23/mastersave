import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/allocation_provider.dart';

class AllocationSetupScreen
    extends ConsumerWidget {
  const AllocationSetupScreen({
    super.key,
  });

  @override
  Widget build(
    BuildContext context,
    WidgetRef ref,
  ) {
    final status =
        ref.watch(
      allocationSetupStatusProvider,
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Set up your allowance',
        ),
      ),

      body: status.when(
        loading: () =>
            const Center(
          child:
              CircularProgressIndicator(),
        ),

        error: (
          error,
          stackTrace,
        ) =>
            Center(
          child: Padding(
            padding:
                const EdgeInsets.all(24),
            child: Text(
              error.toString(),
              textAlign:
                  TextAlign.center,
            ),
          ),
        ),

        data: (data) =>
            _SetupContent(
          status: data,
        ),
      ),
    );
  }
}


class _SetupContent
    extends StatelessWidget {
  final AllocationSetupStatus status;

  const _SetupContent({
    required this.status,
  });

  @override
  Widget build(
    BuildContext context,
  ) {
    return ListView(
      padding:
          const EdgeInsets.all(24),
      children: [
        const Text(
          'Your allowance is ready',
          style: TextStyle(
            fontSize: 28,
            fontWeight:
                FontWeight.w800,
          ),
        ),

        const SizedBox(
          height: 10,
        ),

        const Text(
          'Choose how you want to divide '
          'your money across Spend, Save, '
          'and Grow.',
          style: TextStyle(
            fontSize: 15,
            height: 1.5,
            color:
                Color(0xFF536070),
          ),
        ),

        const SizedBox(
          height: 28,
        ),

        if (status.hasUnallocatedDeposit)
          Container(
            padding:
                const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius:
                  BorderRadius.circular(20),
              border: Border.all(
                color:
                    const Color(0xFFE7E7E7),
              ),
            ),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment
                      .start,
              children: [
                const Text(
                  'Available allowance',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight:
                        FontWeight.w600,
                    color:
                        Color(0xFF8490A0),
                  ),
                ),

                const SizedBox(
                  height: 6,
                ),

                Text(
                  'RWF ${_format(status)}',
                  style:
                      const TextStyle(
                    fontSize: 32,
                    fontWeight:
                        FontWeight.w900,
                  ),
                ),

                const SizedBox(
                  height: 20,
                ),

                SizedBox(
                  width:
                      double.infinity,
                  height: 52,
                  child:
                      ElevatedButton(
                    onPressed: () {
                      // Full setup form
                      // comes next.
                    },
                    child:
                        const Text(
                      'Set up my allowance',
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  String _format(
    AllocationSetupStatus status,
  ) {
    // The endpoint currently exposes
    // allocation amounts, not the actual
    // deposit amount.
    //
    // We therefore temporarily show the
    // Spend + Save + Grow total.
    final total =
        status.spend.allocated +
            status.save.allocated +
            status.grow.allocated;

    return _numberFormat(total);
  }

  String _numberFormat(
    int amount,
  ) {
    final text =
        amount.toString();

    final buffer =
        StringBuffer();

    for (
      var i = 0;
      i < text.length;
      i++
    ) {
      final position =
          text.length - i;

      buffer.write(text[i]);

      if (
        position > 1 &&
        position % 3 == 1
      ) {
        buffer.write(',');
      }
    }

    return buffer.toString();
  }
}