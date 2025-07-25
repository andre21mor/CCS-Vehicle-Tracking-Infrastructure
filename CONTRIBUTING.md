# Contributing to Vehicle Tracking Infrastructure

## Welcome Contributors! 🎉

Thank you for your interest in contributing to the Vehicle Tracking Infrastructure project. This document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Environment details (AWS region, Terraform version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards
4. **Test your changes** thoroughly
5. **Commit with clear messages**: Follow conventional commit format
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request** with detailed description

### Pull Request Guidelines

#### Before Submitting
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Terraform code is formatted (`terraform fmt`)
- [ ] No sensitive information in commits

#### PR Description Should Include
- **What**: Brief description of changes
- **Why**: Reason for the changes
- **How**: Technical approach taken
- **Testing**: How changes were tested
- **Screenshots**: If UI changes are involved

## Development Setup

### Prerequisites
```bash
# Required tools
terraform >= 1.0
aws-cli >= 2.0
git >= 2.0
```

### Local Development
```bash
# Clone your fork
git clone https://github.com/your-username/vehicle-tracking-infrastructure
cd vehicle-tracking-infrastructure

# Set up remote
git remote add upstream https://github.com/original-org/vehicle-tracking-infrastructure

# Create development environment
cp terraform.tfvars.dev terraform.tfvars
terraform init
terraform plan
```

## Coding Standards

### Terraform Code Style
- Use consistent naming conventions
- Add comments for complex logic
- Use variables for reusable values
- Follow module structure patterns
- Include proper resource tags

### Example Terraform Style
```hcl
# Good
resource "aws_lambda_function" "vehicle_processor" {
  function_name = "${var.environment}-vehicle-processor"
  runtime       = "python3.9"
  handler       = "index.handler"
  
  tags = merge(var.common_tags, {
    Name = "Vehicle Processor"
    Type = "Lambda Function"
  })
}

# Avoid
resource "aws_lambda_function" "func1" {
  function_name = "func1"
  runtime = "python3.9"
  handler = "index.handler"
}
```

### Python Code Style (Lambda Functions)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Include docstrings for functions
- Handle errors gracefully
- Use logging instead of print statements

### Documentation Style
- Use clear, concise language
- Include code examples
- Update README when adding features
- Document architectural decisions

## Testing Guidelines

### Infrastructure Testing
```bash
# Validate Terraform syntax
terraform validate

# Check formatting
terraform fmt -check

# Plan without applying
terraform plan
```

### Lambda Function Testing
```bash
# Run unit tests
python -m pytest tests/

# Check code coverage
coverage run -m pytest
coverage report
```

## Architecture Guidelines

### Design Principles
1. **Serverless First**: Prefer managed services
2. **Security by Design**: Implement least privilege
3. **Cost Optimization**: Monitor and optimize costs
4. **Scalability**: Design for growth
5. **Observability**: Include monitoring and logging

### Module Structure
```
modules/module-name/
├── main.tf          # Primary resources
├── variables.tf     # Input variables
├── outputs.tf       # Output values
├── iam.tf          # IAM policies and roles
├── README.md       # Module documentation
└── examples/       # Usage examples
```

## Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately
- [ ] Security review completed
- [ ] Performance impact assessed

## Getting Help

### Resources
- **Documentation**: `/docs` directory
- **Examples**: `/examples` directory
- **API Reference**: `/docs/api`
- **Architecture Decisions**: `/docs/architecture-decisions.md`

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: architecture@company.com (for sensitive issues)

### Mentorship
New contributors are welcome! We provide:
- Code review feedback
- Architecture guidance
- Best practices sharing
- Pair programming sessions (on request)

## Recognition

Contributors will be recognized in:
- Project README
- Release notes
- Annual contributor report

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to Vehicle Tracking Infrastructure!** 🚗✨

Your contributions help make fleet management more efficient and accessible for everyone.
