# Git Conventions for this project
# Conventions version: 1

## Branch naming

feature_prefix: feat
bugfix_prefix: bug
explore_prefix: explore
reopen_suffix: -bugfixing
branch_source: main
blocked_branches: main, master

### Generated branch patterns

| Operation | Pattern |
|-----------|---------|
| New feature | `{feature_prefix}/{NNN}-{short-name}` |
| Bugfix | `{bugfix_prefix}/{NNN}-{short-name}` |
| Explore variant | `{explore_prefix}/{NNN}-{feature}-{variant}` |
| Reopen (from closed) | `{original_prefix}/{NNN}-{short-name}{reopen_suffix}` |

## Commit messages

style: conventional-commits

## Merge behaviour

variant_promotion: --no-ff
always_push: true
push_remote: origin
