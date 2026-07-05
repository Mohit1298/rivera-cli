"""
Namespace Service
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from moorcheh_sdk import MoorchehClient

from rivera.app.utils.errors import NamespaceError


class NamespaceService:
    def __init__(self, moorcheh_client: "MoorchehClient"):
        self.client = moorcheh_client

    def list_namespaces(self) -> list[str]:
        """List all RIVERA namespaces"""
        try:
            all_namespaces = self.client.namespaces.list()

            # Extract namespace names from response
            if isinstance(all_namespaces, dict) and "namespaces" in all_namespaces:
                namespace_list = [
                    ns["namespace_name"] for ns in all_namespaces["namespaces"]
                ]
            else:
                namespace_list = all_namespaces

            # Filter RIVERA namespaces
            rivera_namespaces = [
                ns for ns in namespace_list if ns.startswith("rivera_")
            ]

            return rivera_namespaces

        except Exception as e:
            raise NamespaceError(f"Failed to list namespaces: {e}")
