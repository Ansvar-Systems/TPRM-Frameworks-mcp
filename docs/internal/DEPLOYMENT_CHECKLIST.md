# TPRM Frameworks MCP Server - Deployment Checklist

**Server**: tprm-frameworks-mcp  
**Port**: 8309  
**Date**: 2026-02-07

## Pre-Deployment Checklist

### 1. System Requirements
- [ ] Python 3.10+ installed (`python3 --version`)
- [ ] pip package manager available
- [ ] Git installed (if cloning from repository)
- [ ] 512MB RAM available
- [ ] 100MB disk space available

### 2. Package Installation
- [ ] Repository cloned/accessed: `/Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp`
- [ ] Package installed: `pip3 install -e .`
- [ ] Installation verified: `python3 -c "import tprm_frameworks_mcp"`
- [ ] Command available: `which tprm-mcp`

### 3. Data Files
- [ ] Data directory exists: `src/tprm_frameworks_mcp/data/`
- [ ] SIG Lite data present: `data/sig_lite.json`
- [ ] CAIQ v4 data present: `data/caiq_v4.json`
- [ ] DORA ICT TPP data present: `data/dora_ict_tpp.json`
- [ ] NIS2 Supply Chain data present: `data/nis2_supply_chain.json`
- [ ] Control mappings present: `data/questionnaire-to-scf.json`
- [ ] All JSON files valid: `python3 -m json.tool < data/sig_lite.json`

### 4. Configuration Files
- [ ] `mcp-config.json` created
- [ ] `server.json` updated with health check
- [ ] `.env.example` created
- [ ] `start-server.sh` created and executable (`chmod +x`)
- [ ] `tprm-frameworks-mcp.service` created (Linux)
- [ ] `Makefile` created

### 5. Testing
- [ ] Test suite runs: `python3 test_server.py`
- [ ] All tests pass: "✅ All tests passed!"
- [ ] Health check works: `make check-health`
- [ ] Server starts: `./start-server.sh`
- [ ] Server responds to stdio input

### 6. MCP Configuration
- [ ] MCP config file located
- [ ] Server entry added to config
- [ ] Port 8309 specified
- [ ] Command and args correct
- [ ] Environment variables set
- [ ] MCP client restarted

### 7. Integration Setup
- [ ] security-controls-mcp accessible on port 8308
- [ ] eu-regulations-mcp accessible
- [ ] Cross-server tool calls tested
- [ ] Control mappings verified

## Deployment Steps

### Step 1: Install
```bash
cd /Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp
pip3 install -e .
```
- [ ] Completed without errors

### Step 2: Test
```bash
python3 test_server.py
```
- [ ] All frameworks loaded
- [ ] Evaluation rubric working
- [ ] Control mappings verified
- [ ] Search functionality working

### Step 3: Configure
```bash
# Copy MCP configuration
cat mcp-config.json
# Add to your MCP client configuration file
```
- [ ] Configuration added
- [ ] Syntax validated (valid JSON)
- [ ] Port 8309 set correctly

### Step 4: Deploy
```bash
# For development/testing
./start-server.sh

# For production (Linux)
sudo cp tprm-frameworks-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tprm-frameworks-mcp
sudo systemctl start tprm-frameworks-mcp
```
- [ ] Server started successfully
- [ ] No error messages
- [ ] Health check passing

### Step 5: Verify
```bash
# Check health
make check-health

# Check process
ps aux | grep tprm_frameworks_mcp

# Test tool call
# (via MCP client)
```
- [ ] Health status: "healthy"
- [ ] 4 frameworks loaded
- [ ] 7 tools available
- [ ] Can call `list_frameworks`
- [ ] Can generate questionnaire
- [ ] Can evaluate responses

## Production Readiness

### Data Quality
- [ ] Licensed SIG questionnaires obtained (if using SIG)
- [ ] CAIQ v4 downloaded from CSA (free)
- [ ] DORA/NIS2 questionnaires generated
- [ ] Evaluation rubrics enhanced
- [ ] Control mappings validated

### Performance
- [ ] Tested with large questionnaires (295 questions)
- [ ] Response time acceptable (<2s for generation)
- [ ] Memory usage within limits (<512MB)
- [ ] No memory leaks observed

### Security
- [ ] Input validation implemented
- [ ] File permissions set correctly
- [ ] Sensitive data encrypted (if applicable)
- [ ] Audit logging configured
- [ ] Rate limiting configured (if needed)

### Monitoring
- [ ] Health check endpoint configured
- [ ] Logging configured
- [ ] Log rotation set up
- [ ] Error alerting configured
- [ ] Metrics collection set up

### Documentation
- [ ] DEPLOYMENT.md reviewed
- [ ] INTEGRATION.md reviewed
- [ ] QUICKSTART.md reviewed
- [ ] API documentation accessible
- [ ] Runbook created

### Backup & Recovery
- [ ] Data backup strategy defined
- [ ] Recovery procedure documented
- [ ] Backup tested
- [ ] Questionnaire persistence configured (if needed)

## Post-Deployment Verification

### Functional Testing
- [ ] Test: List frameworks
  ```json
  {"tool": "list_frameworks", "arguments": {}}
  ```
  Expected: 4 frameworks returned

- [ ] Test: Generate questionnaire
  ```json
  {
    "tool": "generate_questionnaire",
    "arguments": {
      "framework": "sig_lite",
      "scope": "lite",
      "entity_type": "cloud_provider"
    }
  }
  ```
  Expected: Questionnaire with questions returned

- [ ] Test: Evaluate response
  ```json
  {
    "tool": "evaluate_response",
    "arguments": {
      "questionnaire_id": "<from_above>",
      "vendor_name": "Test Vendor",
      "responses": [{"question_id": "...", "answer": "Yes"}]
    }
  }
  ```
  Expected: Evaluation results with score

- [ ] Test: Map to controls
  ```json
  {
    "tool": "map_questionnaire_to_controls",
    "arguments": {"framework": "sig_lite"}
  }
  ```
  Expected: SCF control mappings returned

- [ ] Test: Search questions
  ```json
  {
    "tool": "search_questions",
    "arguments": {"query": "encryption", "limit": 5}
  }
  ```
  Expected: Relevant questions returned

### Integration Testing
- [ ] Cross-server call to security-controls-mcp works
- [ ] Cross-server call to eu-regulations-mcp works
- [ ] Data flows correctly between servers
- [ ] Error handling works across servers

### Performance Testing
- [ ] Generate large questionnaire (295 questions)
- [ ] Evaluate 100+ responses
- [ ] Search across all frameworks
- [ ] Concurrent requests handled
- [ ] No performance degradation

### Monitoring Validation
- [ ] Health check returns "healthy"
- [ ] Logs are being written
- [ ] Metrics are being collected
- [ ] Alerts are working
- [ ] Dashboard shows correct status

## Sign-Off

### Pre-Production
- [ ] All checklist items completed
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Team trained on deployment

**Signed**: ________________  
**Date**: ________________

### Production
- [ ] Production deployment successful
- [ ] All integrations verified
- [ ] Monitoring confirmed operational
- [ ] Backup/recovery tested

**Signed**: ________________  
**Date**: ________________

## Rollback Plan

If deployment fails:

1. **Stop Server**
   ```bash
   sudo systemctl stop tprm-frameworks-mcp
   # or
   kill $(cat tprm-mcp.pid)
   ```

2. **Remove MCP Configuration**
   - Remove server entry from MCP config file
   - Restart MCP client

3. **Uninstall Package** (if needed)
   ```bash
   pip3 uninstall tprm-frameworks-mcp
   ```

4. **Restore Previous Version** (if applicable)
   ```bash
   git checkout <previous_commit>
   pip3 install -e .
   ```

5. **Verify Rollback**
   - Check that previous version is running
   - Verify functionality

## Troubleshooting

### Common Issues

**Issue**: Server won't start
- Check: Python version (>= 3.10)
- Check: Package installed (`pip show tprm-frameworks-mcp`)
- Check: Data files present
- Solution: See DEPLOYMENT.md "Troubleshooting" section

**Issue**: MCP client can't connect
- Check: Configuration file syntax (valid JSON)
- Check: Python path in config
- Check: Server is running
- Solution: Restart MCP client after config changes

**Issue**: Tools not working
- Check: Health check status
- Check: Framework data loaded
- Check: Logs for errors
- Solution: See DEPLOYMENT.md for detailed troubleshooting

## Contact Information

**Support Email**: hello@ansvar.eu  
**Documentation**: See DEPLOYMENT.md, INTEGRATION.md, QUICKSTART.md  
**On-Call**: [Define on-call rotation]  
**Escalation**: [Define escalation path]

---

**Checklist Version**: 1.0  
**Last Updated**: 2026-02-07  
**Next Review**: [Schedule regular review]
