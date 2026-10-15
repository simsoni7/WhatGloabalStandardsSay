import type { Metadata } from "next";
export const metadata:Metadata={title:"WGSS · 글로벌 금융업무 지식",description:"금융업무별 실제 화면·표현·다국어 용어를 출처와 함께 비교하는 WGSS"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="ko"><body style={{margin:0}}>{children}</body></html>}
