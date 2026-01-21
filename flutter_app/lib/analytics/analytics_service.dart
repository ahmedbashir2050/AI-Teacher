class AnalyticsService {
  Future<void> logEvent(String name, Map<String, dynamic> params) async {
    // In a real app, send to Segment, Mixpanel, or custom backend
    print('Analytics Event: $name, Params: $params');
  }

  Future<void> setUserProperties(String userId, Map<String, dynamic> properties) async {
    print('Analytics User: $userId, Properties: $properties');
  }
}
