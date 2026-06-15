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
    ListNode* deleteMiddle(ListNode* head) {
        // Handle edge cases
        if (!head) return nullptr;
        if (!head->next) return nullptr;

        // Initialize slow and fast pointers
        ListNode* slow = head;
        ListNode* fast = head;

        // Initialize a node to keep track of the node before the middle node
        ListNode* prevSlow = nullptr;

        // Find the middle node
        while (fast->next && fast->next->next) {
            prevSlow = slow;
            slow = slow->next;
            fast = fast->next->next;
        }

        // If the middle node is the second node, then it's part of a 2-node list or the second half of an odd-length list
        if (slow == head) {
            return head->next;
        } else if (slow->next) {
            prevSlow->next = slow->next;
        } else {
            // If the middle node is the last node, then it's the only node or the second node in a 2-node list
            prevSlow->next = nullptr;
        }

        return head;
    }
};