import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'controller/teacher_dashboard_controller.dart';
import '../../../../core/constants/app_sizes.dart';
import '../../../../analytics/charts/confidence_chart.dart';

class TeacherDashboardScreen extends StatelessWidget {
  const TeacherDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<TeacherDashboardController>();

    return Scaffold(
      appBar: AppBar(title: const Text('Teacher Dashboard')),
      body: Obx(() {
        if (controller.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.p16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('AI Confidence Analytics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: AppSizes.p16),
              const SizedBox(height: 200, child: ConfidenceChart()),
              const SizedBox(height: AppSizes.p24),
              const Text('Answers Pending Review', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: AppSizes.p16),
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: controller.answers.length,
                itemBuilder: (context, index) {
                  final answer = controller.answers[index];
                  return Card(
                    child: ListTile(
                      title: Text(answer['question_text'] ?? 'No Question'),
                      subtitle: Text('Confidence: ${answer['rag_confidence_score']}'),
                      trailing: ElevatedButton(
                        onPressed: () => _showVerifyDialog(context, controller, answer['id']),
                        child: const Text('Verify'),
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        );
      }),
    );
  }

  void _showVerifyDialog(BuildContext context, TeacherDashboardController controller, String answerId) {
    final commentController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Verify Answer'),
        content: TextField(
          controller: commentController,
          decoration: const InputDecoration(labelText: 'Comment'),
        ),
        actions: [
          TextButton(onPressed: () => Get.back(), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              controller.verifyAnswer(answerId, true, commentController.text);
              Get.back();
            },
            child: const Text('Approve'),
          ),
        ],
      ),
    );
  }
}
