let ws: WebSocket | null = null;

export function getWs(): WebSocket | null { return ws; }
export function setWs(w: WebSocket | null) { 
    ws = w;
    return ws
}