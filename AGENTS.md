# IVN Alpaca Deployment SOP (STRICT COMPLIANCE REQUIRED)

Whenever making a code change in this repository, you must follow this exact sequence before uploading or publishing. You are explicitly FORBIDDEN from executing `git commit` or `git push` until you have visibly completed and presented this 7-Step Checklist, and received explicit "Yes" approval from the user:

1. **Test Logic:** Make edits locally and run a script to test that the specific code/logic works against the Alpaca API.
2. **Regression Test:** Test to ensure the change did not break any existing index or crypto strategies.
3. **Backtest / Paper Test:** Verify the change against historical options data or the live paper-trading environment to ensure we don't ruin the strategy's edge.
4. **Documentation:** Update all relevant documentation (README, inline comments, and the required AI Logic write-up).
5. **Compile Check:** Manually run `python -m py_compile <file.py>` to verify syntax.
6. **User Approval:** Present the exact changes to the user and request a clear "Yes" approval.
7. **Publish:** Only after the user approves, commit and push the code.
