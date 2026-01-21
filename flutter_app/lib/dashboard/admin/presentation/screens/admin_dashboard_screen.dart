import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'controller/admin_dashboard_controller.dart';
import '../../../../core/constants/app_sizes.dart';

class AdminDashboardScreen extends StatelessWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<AdminDashboardController>();

    return Scaffold(
      appBar: AppBar(title: const Text('Admin Dashboard')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSizes.p16),
        child: Column(
          children: [
            _buildAdminActionCard(
              title: 'Curriculum Approval',
              description: 'Approve pending educational materials.',
              icon: Icons.assignment_turned_in,
              onTap: () => controller.approveCurriculum('sample-id'),
            ),
            const SizedBox(height: AppSizes.p16),
            _buildAdminActionCard(
              title: 'RAG Reindexing',
              description: 'Force a reindex of the vector database.',
              icon: Icons.storage,
              onTap: () => controller.reindexRAG(),
            ),
            const SizedBox(height: AppSizes.p16),
            _buildAdminActionCard(
              title: 'Audit Trails',
              description: 'View system-wide activity logs.',
              icon: Icons.history,
              onTap: () => Get.toNamed('/audit-logs'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAdminActionCard({
    required String title,
    required String description,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 4,
      child: ListTile(
        leading: Icon(icon, size: 40, color: Colors.blue),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(description),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
