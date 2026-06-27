class Solution {
public:
    int maximumLength(vector<int>& nums) {
        unordered_map<int, int> frequency;
        int maxLength = 0;
        
        for (int num : nums) {
            frequency[num]++;
            int length = 1;
            int k = num;
            
            while (k % 2 == 0) {
                k /= 2;
                if (frequency[k] > 0) {
                    length++;
                } else {
                    break;
                }
            }
            
            if (k == 1) {
                maxLength = max(maxLength, 2 * length - 1);
            } else {
                maxLength = max(maxLength, length);
            }
        }
        
        return maxLength;
    }
};