import 'package:flutter_test/flutter_test.dart';
import 'package:resq_flow/main.dart';

void main() {
  testWidgets('ResQ-Flow app starts', (WidgetTester tester) async {
    await tester.pumpWidget(const ResQFlowApp());

    expect(find.text('ResQ-Flow'), findsOneWidget);
  });
}