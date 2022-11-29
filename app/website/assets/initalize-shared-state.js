import { Subject, shareReplay, concatMap, fromEvent, Observable, withLatestFrom, EMPTY, startWith, switchMap, of, tap, repeat, map, filter, merge, share, distinctUntilChanged, catchError } from 'https://cdn.skypack.dev/pin/rxjs@v7.5.7-j3yWv9lQY9gNeD9CyX5Y/mode=imports,min/optimized/rxjs.js'
import { createCounter } from './create-counter.js';

/**
 * Initalize the state which will be shared between server and client.
 */
export function initalizeSharedState () {
    /**
     * The stream of websockets.
     * A new socket is created every time a socket closes or errors.
     */
     const socket$ = new Observable((subscriber) => {
        const socket = new WebSocket('ws://' + location.host + '/ws')
        subscriber.next(socket)
        subscriber.complete()
    }).pipe(
        switchMap(socket => merge(
            // emit the socket when it becomes open
            fromEvent(socket, 'open').pipe(
                tap(() => console.log('websocket opened')),
                map(() => socket),
            ),
            // on error, close the socket and throw an error
            fromEvent(socket, 'error').pipe(
                tap((err) => {
                    socket.close()
                    throw err
                })
            ),
            // on close, throw an error
            fromEvent(socket, 'close').pipe(
                tap(() => {
                    throw new Error('Websocket closed!')
                }),
            )
        )),
        catchError(err => {
            console.error(err)
            return of(null)
        }),
        repeat({ delay: 1000 }),
        startWith(null),
        distinctUntilChanged(),
        shareReplay(1)
    )
    
    socket$.subscribe(s => console.log('socket', s))

    // keep track of which messages have been processed
    // (this is crucial for the locking mechanism)
    const unprocessedMessageIds = new Set()
    const generateUnprocessedMessageId = (function(){
        const idIterator = createCounter()
        return () => {
            const newId = idIterator.next().value
            unprocessedMessageIds.add(newId)
        }
    })()

    /**
     * Stream of parsed messages coming from the sockets.
     */
    const message$ = socket$.pipe(
        filter(socket => socket),
        switchMap(socket => fromEvent(socket, 'message')),
        concatMap((msg) => {
            try {
                return of(JSON.parse(msg.data))
            } catch (err) {
                return EMPTY
            }
        }),
        tap((msg) => {
            if (!msg.processedIds) {
                return
            }
            for (const processedId of msg.processedIds) {
                unprocessedMessageIds.delete(processedId)
            }
        }),
        share()
    )
    
    message$.subscribe(m => console.log('message', m))

    /**
     * Stream which includes updates coming from the sockets targeting both client and server states.
     * The stream normally outputs
     *   1. Right after the connection has been made
     *   2. When the connection closes
     */
    const fullStateUpdate$ = merge(
        message$.pipe(
            filter(({ type, data }) => type === 'full-state-update'),
            map(message => message.data)
        ),
        socket$.pipe(
            filter(socket => socket === null),
            map(() => ({
                clientState: null,
                serverState: null
            }))
        )
    ).pipe(
        share()
    )

    // make it possible for the client to emit a new server state
    const serverStateSubject$ = new Subject()
    function updateServerState (serverState) {
        serverStateSubject$.next(serverState)
    }

    // if the client emits new server states, send them to the server,
    // and lock the server state until the server processes the new state
    serverStateSubject$.pipe(
        withLatestFrom(socket$)
    ).subscribe(([serverState, socket]) => {
        const id = generateUnprocessedMessageId()
        socket?.send(JSON.stringify({
            type: 'server-state-update',
            id,
            data: serverState
        }))
    })

    /**
     * Stream which includes updates coming from the sockets targeting the server state.
     * The stream outputs often, e.g. when the Raspberry Pi leaves a node.
     * Outputs null when the socket is closed.
     */
    const serverStateUpdate$ = merge(
        fullStateUpdate$.pipe(
            map(data => data.serverState)
        ),
        message$.pipe(
            tap((message) => {
                console.log('new serverState message!', message, 'unprocessed message IDs', unprocessedMessageIds)
            }),
            filter(message =>
                message.type === 'server-state-update'
                && unprocessedMessageIds.size === 0
            ),
            map(message => message.data)
        )
    ).pipe(
        share()
    )

    /**
     * Stream which includes updates coming from the sockets targeting the client state. 
     */
    const clientStateUpdate$ = merge(
        fullStateUpdate$.pipe(
            map(data => data.clientState)
        )
    ).pipe(
        share()
    )

    // make it possible for the client to emit new client state
    const clientStateSubject$ = new Subject()
    function updateClientState (clientState) {
        clientStateSubject$.next(clientState)
    }

    // if the client emits new states, send them to the server
    clientStateSubject$.pipe(
        withLatestFrom(socket$)
    ).subscribe(([clientState, socket]) => {
        socket?.send(JSON.stringify({
            type: 'client-state-update',
            data: clientState
        }))
    })

    const serverState$ = merge(
        serverStateSubject$,
        serverStateUpdate$
    ).pipe(
        startWith(null),
        distinctUntilChanged(),
        tap(x => console.log('SERVER STATE CHANGED', x)),
        shareReplay(1)
    )

    const clientState$ = merge(
        clientStateSubject$,
        clientStateUpdate$
    ).pipe(
        startWith(null),
        distinctUntilChanged(),
        tap(x => console.log('CLIENT STATE CHANGED', x)),
        shareReplay(1)
    )

    return {
        updateServerState,
        updateClientState,
        serverStateUpdate$,
        serverState$,
        clientStateUpdate$,
        clientState$
    }
}