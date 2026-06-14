/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode() : val(0), next(nullptr) {}
 *     ListNode(int x) : val(x), next(nullptr) {}
 *     ListNode(int x, ListNode *next) : val(x), next(next) {}
 * };
 */
class Solution {
public:
    int pairSum(ListNode* head) {
        // Convert linked list to vector for easier access
        std::vector<int> values;
        while (head) {
            values.push_back(head->val);
            head = head->next;
        }

        int maxSum = INT_MIN;  // Initialize with negative infinity
        int n = values.size();

        // Calculate sum of each pair and update maxSum
        for (int i = 0; i < n / 2; i++) {
            maxSum = std::max(maxSum, values[i] + values[n - 1 - i]);
        }

        return maxSum;
    }
};