
To finalize the backend architecture, we are refining the **User** model to include both a numerical primary key for database efficiency and a string-based identifier for LDAP/Login purposes. This structure ensures high-performance joins while maintaining the JSON flexibility needed for evolving user profiles.

---

# **Technical Specification: SQLAlchemy Backend (V5.1)**

## **1. Refined Database Schema**

The system utilizes **SQLite** by default. The relational design ensures referential integrity between users and their analytical workspaces through a dedicated liaison table.

### **1.1 Table: `users`**

| **Column**      | **Type** | **Constraints** | **Description**                      |
| --------------------- | -------------- | --------------------- | ------------------------------------------ |
| **`id`**      | `Integer`    | Primary Key, Auto-inc | Internal numerical identifier.             |
| **`user_id`** | `String`     | Unique, Indexed       | LDAP/Login string identifier.              |
| **`profile`** | `JSON`       | Default `{}`        | Flexible storage for UI settings/metadata. |
| **`enabled`** | `Boolean`    | Default `True`      | Global toggle for account access.          |

### **1.2 Table: `workspaces`**

| **Column**          | **Type** | **Constraints** | **Description**                  |
| ------------------------- | -------------- | --------------------- | -------------------------------------- |
| **`id`**          | `String`     | Primary Key (UUID)    | Unique workspace identifier.           |
| **`name`**        | `String`     | Required              | Friendly session name.                 |
| **`state`**       | `JSON`       | Default `{}`        | The 50-pane pool, history, and layout. |
| **`is_archived`** | `Boolean`    | Default `False`     | Soft-delete flag (visible vs. hidden). |
| **`updated_at`**  | `DateTime`   | Auto-update           | Used for "Recently Viewed" sorting.    |

### **1.3 Table: `workspace_members`**

| **Column**           | **Type** | **Constraints**  | **Description**              |
| -------------------------- | -------------- | ---------------------- | ---------------------------------- |
| **`workspace_id`** | `String`     | FK (`workspaces.id`) | Reference to the workspace.        |
| **`user_id`**      | `Integer`    | FK (`users.id`)      | Reference to the internal user ID. |
| **`role`**         | `String`     | 'OWNER' or 'EDITOR'    | Defines terminal permissions.      |

---

## **2. Backend Implementation (SQLAlchemy)**

This implementation uses standard SQLAlchemy declarations to define the relationships and the liaison logic.

**Python**

```
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
  
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False) # LDAP Login
    profile = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
  
    # Relationship to memberships
    memberships = relationship("WorkspaceMember", back_populates="user")

class Workspace(Base):
    __tablename__ = "workspaces"
  
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    state = Column(JSON, default={"panes": [], "visibleIds": []})
    is_archived = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  
    members = relationship("WorkspaceMember", back_populates="workspace")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
  
    workspace_id = Column(String, ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String, default="VIEWER") # OWNER, EDITOR, VIEWER
  
    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="members")
```

---

## **3. Automated Smart Pruning Logic**

To manage the  **50-pane limit** , the backend supports the frontend's pruning request by validating lineage. A pane **$P$** is considered an "Orphan" and eligible for removal if it satisfies:

$$
P_{\text{prunable}} \iff (P \notin \text{ActiveGrid}) \land (\neg P.\text{is\_sticky}) \land (\text{Children}(P) = \emptyset)
$$

By persisting the `state` as a JSON blob, the backend remains agnostic of the specific lineage graph, while the relational `WorkspaceMember` table ensures only the `OWNER` or `EDITOR` can trigger the `/prune` operation.

---

## **4. Supported Operations**

* **User Synchronization:** On LDAP login, the system verifies if `user_id` exists. If not, it creates a new record with `enabled=True`.
* **Workspace Retrieval:** Fetches all non-archived workspaces for a specific `user_id` by joining through the `workspace_members` table.
* **State Persistence:** The terminal-centric frontend debounces state changes (pane creation, movement, or text updates) and pushes them to the `workspaces.state` JSON column.
* **Soft Removal:** Deleting a workspace via the terminal (`/rm workspace`) sets `is_archived=True`, effectively hiding it from the user list while preserving the audit trail in SQLite.

## **5. Why This Design Works**

1. **Fast Lookups:** Using a numerical `id` for primary keys and foreign keys makes joins across users and members extremely fast in SQLite.
2. **Schema Flexibility:** The `profile` and `state` JSON fields allow you to add new features (like custom terminal themes or new pane types) without ever needing to run an `ALTER TABLE` command.
3. **Audit Ready:** Since we never delete rows from `workspaces`, you can implement a "Restore Session" feature in the future by simply toggling the `is_archived` flag.

Would you like me to create a **sample initialization script** that creates the SQLite database file and seeds it with a test user and an initial empty workspace?

To finalize the backend architecture, we are refining the **User** model to include both a numerical primary key for database efficiency and a string-based identifier for LDAP/Login purposes. This structure ensures high-performance joins while maintaining the JSON flexibility needed for evolving user profiles.

---

# **Technical Specification: SQLAlchemy Backend (V5.1)**

## **1. Refined Database Schema**

The system utilizes **SQLite** by default. The relational design ensures referential integrity between users and their analytical workspaces through a dedicated liaison table.

### **1.1 Table: `users`**

| **Column**      | **Type** | **Constraints** | **Description**                      |
| --------------------- | -------------- | --------------------- | ------------------------------------------ |
| **`id`**      | `Integer`    | Primary Key, Auto-inc | Internal numerical identifier.             |
| **`user_id`** | `String`     | Unique, Indexed       | LDAP/Login string identifier.              |
| **`profile`** | `JSON`       | Default `{}`        | Flexible storage for UI settings/metadata. |
| **`enabled`** | `Boolean`    | Default `True`      | Global toggle for account access.          |

### **1.2 Table: `workspaces`**

| **Column**          | **Type** | **Constraints** | **Description**                  |
| ------------------------- | -------------- | --------------------- | -------------------------------------- |
| **`id`**          | `String`     | Primary Key (UUID)    | Unique workspace identifier.           |
| **`name`**        | `String`     | Required              | Friendly session name.                 |
| **`state`**       | `JSON`       | Default `{}`        | The 50-pane pool, history, and layout. |
| **`is_archived`** | `Boolean`    | Default `False`     | Soft-delete flag (visible vs. hidden). |
| **`updated_at`**  | `DateTime`   | Auto-update           | Used for "Recently Viewed" sorting.    |

### **1.3 Table: `workspace_members`**

| **Column**           | **Type** | **Constraints**  | **Description**              |
| -------------------------- | -------------- | ---------------------- | ---------------------------------- |
| **`workspace_id`** | `String`     | FK (`workspaces.id`) | Reference to the workspace.        |
| **`user_id`**      | `Integer`    | FK (`users.id`)      | Reference to the internal user ID. |
| **`role`**         | `String`     | 'OWNER' or 'EDITOR'    | Defines terminal permissions.      |

---

## **2. Backend Implementation (SQLAlchemy)**

This implementation uses standard SQLAlchemy declarations to define the relationships and the liaison logic.

**Python**

```
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
  
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False) # LDAP Login
    profile = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
  
    # Relationship to memberships
    memberships = relationship("WorkspaceMember", back_populates="user")

class Workspace(Base):
    __tablename__ = "workspaces"
  
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    state = Column(JSON, default={"panes": [], "visibleIds": []})
    is_archived = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  
    members = relationship("WorkspaceMember", back_populates="workspace")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
  
    workspace_id = Column(String, ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String, default="VIEWER") # OWNER, EDITOR, VIEWER
  
    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="members")
```

---

## **3. Automated Smart Pruning Logic**

To manage the  **50-pane limit** , the backend supports the frontend's pruning request by validating lineage. A pane **$P$** is considered an "Orphan" and eligible for removal if it satisfies:

$$
P_{\text{prunable}} \iff (P \notin \text{ActiveGrid}) \land (\neg P.\text{is\_sticky}) \land (\text{Children}(P) = \emptyset)
$$

By persisting the `state` as a JSON blob, the backend remains agnostic of the specific lineage graph, while the relational `WorkspaceMember` table ensures only the `OWNER` or `EDITOR` can trigger the `/prune` operation.

---

## **4. Supported Operations**

* **User Synchronization:** On LDAP login, the system verifies if `user_id` exists. If not, it creates a new record with `enabled=True`.
* **Workspace Retrieval:** Fetches all non-archived workspaces for a specific `user_id` by joining through the `workspace_members` table.
* **State Persistence:** The terminal-centric frontend debounces state changes (pane creation, movement, or text updates) and pushes them to the `workspaces.state` JSON column.
* **Soft Removal:** Deleting a workspace via the terminal (`/rm workspace`) sets `is_archived=True`, effectively hiding it from the user list while preserving the audit trail in SQLite.

## **5. Why This Design Works**

1. **Fast Lookups:** Using a numerical `id` for primary keys and foreign keys makes joins across users and members extremely fast in SQLite.
2. **Schema Flexibility:** The `profile` and `state` JSON fields allow you to add new features (like custom terminal themes or new pane types) without ever needing to run an `ALTER TABLE` command.
3. **Audit Ready:** Since we never delete rows from `workspaces`, you can implement a "Restore Session" feature in the future by simply toggling the `is_archived` flag.

Would you like me to create a **sample initialization script** that creates the SQLite database file and seeds it with a test user and an initial empty workspace?
