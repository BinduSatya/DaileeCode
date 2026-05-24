class Solution {
public:
    int maxJumps(vector<int>& arr, int d) {
        int n = arr.size();
        vector<int> memo(n, -1);
        
        int result = 0;
        for (int i = 0; i < n; i++) {
            result = max(result, dfs(arr, d, memo, i));
        }
        
        return result;
    }
    
    int dfs(vector<int>& arr, int d, vector<int>& memo, int i) {
        if (memo[i] != -1) {
            return memo[i];
        }
        
        int maxJumps = 1;
        for (int j = max(0, i - d); j <= min((int)arr.size() - 1, i + d); j++) {
            if (i == j) {
                continue;
            }
            
            if (arr[i] > arr[j]) {
                bool canJump = true;
                if (j < i) {
                    for (int k = j + 1; k < i; k++) {
                        if (arr[k] >= arr[j]) {
                            canJump = false;
                            break;
                        }
                    }
                } else {
                    for (int k = i + 1; k < j; k++) {
                        if (arr[k] >= arr[j]) {
                            canJump = false;
                            break;
                        }
                    }
                }
                
                if (canJump) {
                    maxJumps = max(maxJumps, 1 + dfs(arr, d, memo, j));
                }
            }
        }
        
        memo[i] = maxJumps;
        return maxJumps;
    }
};