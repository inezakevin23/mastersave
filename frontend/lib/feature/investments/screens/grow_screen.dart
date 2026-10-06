import 'package:flutter/material.dart';

class GrowScreen extends StatelessWidget {
  const GrowScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Grow')),

      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Grow your money',
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800),
          ),

          const SizedBox(height: 8),

          const Text(
            'Explore available investment products.',
            style: TextStyle(color: Color(0xFF697586)),
          ),

          const SizedBox(height: 24),

          SizedBox(
            height: 52,
            child: ElevatedButton.icon(
              onPressed: () {
                // Investment products next.
              },
              icon: const Icon(Icons.trending_up),
              label: const Text('Explore investments'),
            ),
          ),
        ],
      ),
    );
  }
}
