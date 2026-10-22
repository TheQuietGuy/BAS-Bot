import { useCallback, useState } from "react";
import type { ReactNode } from "react";
import { ConfirmDialog } from "../components/ConfirmDialog";

interface ConfirmOptions {
  title: string;
  body: string;
  confirmLabel: string;
}

// Usage: const { confirm, dialog } = useConfirm();
//        if (await confirm({...})) { ...do the destructive thing... }
//        and render {dialog} somewhere in the page.
export function useConfirm() {
  const [state, setState] = useState<
    (ConfirmOptions & { resolve: (ok: boolean) => void }) | null
  >(null);

  const confirm = useCallback(
    (options: ConfirmOptions) =>
      new Promise<boolean>((resolve) => setState({ ...options, resolve })),
    []
  );

  const close = (ok: boolean) => {
    state?.resolve(ok);
    setState(null);
  };

  const dialog: ReactNode = state ? (
    <ConfirmDialog
      title={state.title}
      body={state.body}
      confirmLabel={state.confirmLabel}
      onConfirm={() => close(true)}
      onCancel={() => close(false)}
    />
  ) : null;

  return { confirm, dialog };
}
