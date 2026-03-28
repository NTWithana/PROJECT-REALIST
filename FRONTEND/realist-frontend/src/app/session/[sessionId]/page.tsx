import WorkspaceShell from "./WorkspaceShell";
import SessionLayout from "./SessionLayout";

export default async function Page({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;

  return (
    <WorkspaceShell sessionId={sessionId}>
      <SessionLayout sessionId={sessionId} />
    </WorkspaceShell>
  );
}
