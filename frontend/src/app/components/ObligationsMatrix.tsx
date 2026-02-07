export function ObligationsMatrix({
  matrix,
  banks,
  title,
}: {
  matrix: number[][];
  banks: string[];
  title: string;
}) {
  const max = Math.max(...matrix.flat(), 0.01);
  return (
    <div className="flex flex-col items-center">
      <h3 className="mb-3 text-sm font-semibold text-zinc-300">{title}</h3>
      <div className="overflow-x-auto w-full flex justify-center">
        <table className="text-xs font-mono">
          <thead>
            <tr>
              <th className="p-1" />
              {banks.map((b) => (
                <th key={b} className="p-1 text-zinc-500 font-normal">
                  {b}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                <td className="pr-2 text-zinc-500">{banks[i]}</td>
                {row.map((val, j) => {
                  const intensity = i === j ? 0 : val / max;
                  return (
                    <td
                      key={j}
                      className="p-1 text-center rounded"
                      style={{
                        backgroundColor:
                          i === j
                            ? "transparent"
                            : `rgba(239,68,68,${intensity * 0.7})`,
                        color: intensity > 0.4 ? "#fff" : "#a1a1aa",
                      }}
                    >
                      {i === j ? "—" : val.toFixed(1)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
