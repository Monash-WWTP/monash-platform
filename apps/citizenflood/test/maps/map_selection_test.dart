import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/maps/map_selection.dart';

void main() {
  test('observation and report location selections are independent', () {
    final state = MapSelection();
    state.selectObservation('observation');
    expect(state.location, isNull);
    expect(state.observationId, 'observation');
    state.chooseLocation(
      const SelectedLocation(
        latitude: 3,
        longitude: 101,
        source: LocationSource.selected,
      ),
    );
    expect(state.location!.latitude, 3);
    state.clear();
    expect(state.location, isNull);
    expect(state.observationId, isNull);
  });
}
