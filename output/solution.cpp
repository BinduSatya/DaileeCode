class Solution {
public:
    int maxNumberOfBalloons(string text) {
        // Count frequency of each character in the string
        unordered_map<char, int> freq;
        for (char c : text) {
            freq[c]++;
        }
        
        // Calculate the maximum number of "balloon" instances
        return min({freq['b'], freq['a'], freq['l'] / 2, freq['o'] / 2, freq['n']});
    }
};