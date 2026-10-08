from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import supabase


# ============================================================
# Authentication Configuration
# ============================================================

security = HTTPBearer()


# ============================================================
# Get Current User
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validate the Supabase access token and return the
    authenticated user.
    """

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        return response.user

    except HTTPException:
        raise

    except Exception as e:
        print("AUTHENTICATION ERROR:", e)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# ============================================================
# Role Authorization
# ============================================================

def require_role(*allowed_roles):
    """
    Restrict an endpoint to specific user roles.

    Example:
        Depends(require_role("RESCUER", "ADMIN"))
    """

    def role_checker(
        current_user=Depends(get_current_user)
    ):
        try:
            response = (
                supabase
                .table("profiles")
                .select("role")
                .eq("id", current_user.id)
                .maybe_single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User profile not found"
                )

            user_role = response.data["role"]

            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to perform this action"
                )

            return current_user

        except HTTPException:
            raise

        except Exception as e:
            print("ROLE AUTHORIZATION ERROR:", e)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify user permissions"
            )

    return role_checker