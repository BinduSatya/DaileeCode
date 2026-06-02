class Solution {
public:
    int earliestFinishTime(vector<int>& landStartTime, vector<int>& landDuration, vector<int>& waterStartTime, vector<int>& waterDuration) {
        int minTime = INT_MAX;
        
        // Land ride first
        for (int i = 0; i < landStartTime.size(); i++) {
            for (int j = 0; j < waterStartTime.size(); j++) {
                int finishTime = max(landStartTime[i] + landDuration[i], waterStartTime[j]) + waterDuration[j];
                minTime = min(minTime, finishTime);
            }
        }
        
        // Water ride first
        for (int i = 0; i < waterStartTime.size(); i++) {
            for (int j = 0; j < landStartTime.size(); j++) {
                int finishTime = max(waterStartTime[i] + waterDuration[i], landStartTime[j]) + landDuration[j];
                minTime = min(minTime, finishTime);
            }
        }
        
        return minTime;
    }
};