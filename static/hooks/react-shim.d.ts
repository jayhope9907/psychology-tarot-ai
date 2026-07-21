/** Minimal React ambient types for standalone `tsc` without node_modules. */
declare module "react" {
  export function useCallback<T extends (...args: never[]) => unknown>(
    fn: T,
    deps: readonly unknown[]
  ): T;
  export function useRef<T>(initial: T): { current: T };
  export function useState<S>(
    initial: S | (() => S)
  ): [S, (next: S | ((prev: S) => S)) => void];
}
