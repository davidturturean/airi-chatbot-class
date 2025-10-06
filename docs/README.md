# AIRI Chatbot Documentation

This directory contains comprehensive documentation for the AIRI Chatbot project.

## Quick Navigation

### For New Developers
- [Main README](../README.md) - Installation and basic usage
- [Architecture Overview](architecture/MESSAGE_PROCESSING_LOGIC.md) - How the system works
- [RAG System Guide](architecture/rag_system.md) - Understanding retrieval architecture
- [Implementation Status](architecture/implementation_status.md) - Current features

### For Deployers
- [Deployment Guide](deployment/deployment_guide.md) - Complete deployment instructions
- [Decision Matrix](deployment/decision_matrix.md) - Choosing deployment options
- [Deployment Gates](deployment/gates_reference.md) - Pre-deployment checklist
- [Running Lean](deployment/running_lean.md) - Optimizing resource usage
- [Executive Summary](deployment/executive_summary.md) - High-level deployment overview

### For Testers
- [Testing Brief](testing/testing_brief.md) - Comprehensive testing guide
- [Pre-Testing Checklist](testing/pre_testing_checklist.md) - What to verify before testing
- [Readiness Checklist](testing/readiness_checklist.md) - Is the system ready for testing?
- [Session Transfer Tests](testing/session_transfer.md) - Testing session functionality
- [Supervisor Briefing](testing/supervisor_briefing.md) - For test supervisors
- [Google Form Setup](testing/google_form_instructions.md) - Setting up feedback forms
- [UI Feedback Plan](testing/ui_feedback_plan.md) - User interface testing

### For Webflow Integration
- [Integration Overview](webflow/widget_integration.md) - How to integrate the chatbot
- [Session Integration](webflow/session_integration.md) - Session management in Webflow
- [Analytics Setup](webflow/analytics_setup.md) - PostHog analytics configuration
- [Password Setup](webflow/password_setup.md) - Securing the chatbot
- [Metrics Dashboard](webflow/metrics_dashboard.md) - Viewing analytics
- [Analytics Plan](webflow/analytics_plan.md) - Analytics strategy
- [Chatbot Page Files](webflow/chatbot_page/) - HTML/JS for chatbot page

### Architecture & Technical Details
- [Message Processing Logic](architecture/MESSAGE_PROCESSING_LOGIC.md) - How messages are processed
- [RAG System](architecture/rag_system.md) - Retrieval-Augmented Generation details
- [Performance Plan](architecture/performance_plan.md) - Performance optimization strategies
- [Synthesis Improvements](architecture/synthesis_improvements.md) - Response generation improvements
- [Snippet System](architecture/snippet_system.md) - Citation and snippet management

## Directory Structure

```
docs/
├── README.md                 # This file
├── architecture/             # System architecture and technical documentation
├── deployment/               # Deployment guides and configurations
├── testing/                  # Testing plans, briefs, and checklists
├── webflow/                  # Webflow integration documentation and code
└── archive/                  # Deprecated or historical documentation
```

## Common Tasks

### I want to modify the RAG retrieval method
See [RAG System Guide](architecture/rag_system.md) and [Modifying RAG](architecture/modifying_rag.md)

### I want to deploy the chatbot
Start with [Deployment Guide](deployment/deployment_guide.md), then check [Decision Matrix](deployment/decision_matrix.md)

### I want to integrate with Webflow
Follow [Widget Integration](webflow/widget_integration.md) guide

### I want to run tests
Review [Testing Brief](testing/testing_brief.md) and [Pre-Testing Checklist](testing/pre_testing_checklist.md)

### I want to understand how messages are processed
Read [Message Processing Logic](architecture/MESSAGE_PROCESSING_LOGIC.md)

## Maintenance and Contribution

### For Maintainers
- [Maintenance Guide](MAINTENANCE.md) - How to keep the codebase organized
- [Cleanup Summary](CLEANUP_SUMMARY.md) - What was reorganized and why

### Contributing to Documentation

When adding new documentation:
- Place it in the appropriate subdirectory
- Update this README.md with a link
- Use clear, descriptive filenames
- Include a brief summary at the top of each document
- Follow the maintenance guide rules

See [Maintenance Guide](MAINTENANCE.md) for detailed file organization rules.

## Need Help?

If you can't find what you're looking for:
1. Check the [Main README](../README.md)
2. Review the [Implementation Status](architecture/implementation_status.md)
3. Check the [Maintenance Guide](MAINTENANCE.md) for file organization
4. Search for keywords across all documentation files
