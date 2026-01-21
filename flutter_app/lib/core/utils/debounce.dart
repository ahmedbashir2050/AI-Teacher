import 'dart:async';

class Debounce {
  final int milliseconds;
  Timer? _timer;

  Debounce({required this.milliseconds});

  void run(void Function() action) {
    _timer?.cancel();
    _timer = Timer(Duration(milliseconds: milliseconds), action);
  }

  void dispose() {
    _timer?.cancel();
  }
}
