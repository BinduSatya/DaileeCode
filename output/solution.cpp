class Solution {
public:
    double angleClock(int hour, int minutes) {
        double hourAngle = (hour % 12 + minutes / 60.0) * 30;
        double minuteAngle = minutes * 6;
        double angle = abs(hourAngle - minuteAngle);
        return min(angle, 360 - angle);
    }
};