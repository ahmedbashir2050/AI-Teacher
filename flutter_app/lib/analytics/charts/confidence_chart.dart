import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class ConfidenceChart extends StatelessWidget {
  const ConfidenceChart({super.key});

  @override
  Widget build(BuildContext context) {
    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: true),
        lineBarsData: [
          LineChartBarData(
            spots: [
              const FlSpot(0, 0.85),
              const FlSpot(1, 0.90),
              const FlSpot(2, 0.88),
              const FlSpot(3, 0.95),
              const FlSpot(4, 0.92),
            ],
            isCurved: true,
            barWidth: 3,
            color: Colors.blue,
          ),
        ],
      ),
    );
  }
}
