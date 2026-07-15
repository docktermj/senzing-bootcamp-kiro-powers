# AWS SSO login

## Steps

1. In Kiro:
   1. Click "Sign in"
1. In web browser:
   1. In "Choose a way to sign in/up":
      1. Click "Your organization".
   1. In "Sign in with your organization":
      1. Click on the "Sign in via IAM Identity Center instead" link.
   1. In "Sign in with AWS IAM Identity Center":
      1. **Start URL:**  Enter your organization's IAM Identity Center start URL
         (ask your AWS administrator if you don't have it).
      1. **AWS Region:**  Enter your organization's region.
         Example:

         ```console
         us-east-1
         ```

      1. Click "Continue"
   1. In your organization's sign-in page:
      1. **Username:**  Enter your SSO username.
      1. Click "Next"
      1. **Password:**  Enter your SSO password.
      1. Click "Sign in"
   1. In "Additional verification required":
      1. **MFA code:**  You are on your own for this one!
      1. Click "Sign in"
   1. In "Allow Kiro IDE to access your data?":
      1. Click "Allow access"
