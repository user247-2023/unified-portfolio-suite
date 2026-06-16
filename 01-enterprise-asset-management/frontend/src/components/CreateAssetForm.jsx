/**
 * CreateAssetForm component.
 * Purpose: Controlled form to register a new asset. Disabled (with an
 * explanation) when the current actor lacks the admin role — surfacing the
 * default-deny RBAC rule in the UI.
 */
import React, { useState } from "react";

export default function CreateAssetForm({ canEdit, onCreate }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("hardware");

  function submit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    onCreate({ name: name.trim(), category });
    setName("");
  }

  return (
    <form className="create-form" onSubmit={submit}>
      <input
        aria-label="Asset name"
        placeholder="Asset name (e.g. ThinkPad X1)"
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={!canEdit}
      />
      <select
        aria-label="Category"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        disabled={!canEdit}
      >
        <option value="hardware">hardware</option>
        <option value="software">software</option>
        <option value="license">license</option>
      </select>
      <button type="submit" disabled={!canEdit}>
        Add asset
      </button>
      {!canEdit && (
        <span className="hint">Switch to the admin role to add assets.</span>
      )}
    </form>
  );
}
