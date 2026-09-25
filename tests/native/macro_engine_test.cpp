#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "macro_engine.h"

static int g_callbackDispatches = 0;
static uint32_t g_lastDispatchedId = 0;

static void testCallback(const macro_engine::StepResult& result, void* /*userData*/) {
  g_callbackDispatches++;
  g_lastDispatchedId = result.macroId;
}

int main() {
  using namespace macro_engine;

  // 1. Gesture enum and string parser tests
  assert(strcmp(gestureToString(Gesture::Left), "LEFT") == 0);
  assert(strcmp(gestureToString(Gesture::Right), "RIGHT") == 0);
  assert(strcmp(gestureToString(Gesture::Up), "UP") == 0);
  assert(strcmp(gestureToString(Gesture::Down), "DOWN") == 0);
  assert(strcmp(gestureToString(Gesture::Circle), "CIRCLE") == 0);
  assert(strcmp(gestureToString(Gesture::CircleCcw), "CIRCLE_CCW") == 0);
  assert(strcmp(gestureToString(Gesture::Shake), "SHAKE") == 0);
  assert(strcmp(gestureToString(Gesture::Push), "PUSH") == 0);
  assert(strcmp(gestureToString(Gesture::Stop), "STOP") == 0);
  assert(strcmp(gestureToString(Gesture::Unknown), "UNKNOWN") == 0);

  assert(gestureFromString("left") == Gesture::Left);
  assert(gestureFromString("LEFT") == Gesture::Left);
  assert(gestureFromString("swipe_left") == Gesture::Left);
  assert(gestureFromString("SWIPE_LEFT") == Gesture::Left);
  assert(gestureFromString("right") == Gesture::Right);
  assert(gestureFromString("swipe_right") == Gesture::Right);
  assert(gestureFromString("up") == Gesture::Up);
  assert(gestureFromString("swipe_up") == Gesture::Up);
  assert(gestureFromString("down") == Gesture::Down);
  assert(gestureFromString("swipe_down") == Gesture::Down);
  assert(gestureFromString("circle") == Gesture::Circle);
  assert(gestureFromString("circle_clockwise") == Gesture::Circle);
  assert(gestureFromString("circle_ccw") == Gesture::CircleCcw);
  assert(gestureFromString("circle_counter_clockwise") == Gesture::CircleCcw);
  assert(gestureFromString("shake") == Gesture::Shake);
  assert(gestureFromString("push") == Gesture::Push);
  assert(gestureFromString("stop") == Gesture::Stop);
  assert(gestureFromString("x") == Gesture::Stop);
  assert(gestureFromString("unknown") == Gesture::Unknown);
  assert(gestureFromString("arbitrary_garbage") == Gesture::Unknown);
  assert(gestureFromString(nullptr) == Gesture::Unknown);

  assert(isDirectional(Gesture::Left));
  assert(isDirectional(Gesture::Right));
  assert(isDirectional(Gesture::Up));
  assert(isDirectional(Gesture::Down));
  assert(isDirectional(Gesture::Circle));
  assert(!isDirectional(Gesture::Shake));
  assert(!isDirectional(Gesture::Push));
  assert(!isDirectional(Gesture::Stop));
  assert(!isDirectional(Gesture::Unknown));

  // 2. Registration and capacity tests
  MacroEngine engine;
  assert(engine.getMacroCount() == 0);
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);
  assert(engine.getTimeoutMs() == kDefaultTimeoutMs);

  // Register MACRO_01: LEFT -> RIGHT -> CIRCLE
  bool regOk = engine.registerMacro(1, "MACRO_01", {Gesture::Left, Gesture::Right, Gesture::Circle}, 42);
  assert(regOk);
  assert(engine.getMacroCount() == 1);
  const MacroDefinition* m1 = engine.findMacroById(1);
  assert(m1 != nullptr);
  assert(strcmp(m1->name, "MACRO_01") == 0);
  assert(m1->length == 3);
  assert(m1->actionPayload == 42);
  assert(engine.findMacroByName("macro_01") == m1);

  // Reject sequence containing Unknown
  assert(!engine.registerMacro(2, "BAD_UNKNOWN", {Gesture::Left, Gesture::Unknown, Gesture::Right}));
  // Reject empty sequence
  const Gesture emptySeq[1] = {Gesture::Left};
  assert(!engine.registerMacro(3, "EMPTY", emptySeq, 0));

  // 3. Normal recognition sequence: LEFT -> RIGHT -> CIRCLE
  engine.setDispatchCallback(testCallback, nullptr);

  // Step 1: Left
  StepResult res1 = engine.feed(Gesture::Left, 1000);
  assert(res1.status == StepStatus::Progress);
  assert(!res1.actionTriggered);
  assert(res1.currentStep == 1);
  assert(res1.expectedTotal == 3);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);
  assert(g_callbackDispatches == 0);

  // Step 2: Right (within timeout window)
  StepResult res2 = engine.feed(Gesture::Right, 1600);
  assert(res2.status == StepStatus::Progress);
  assert(!res2.actionTriggered);
  assert(res2.currentStep == 2);
  assert(res2.expectedTotal == 3);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 2);
  assert(g_callbackDispatches == 0);

  // Step 3: Circle -> Full sequence completion
  StepResult res3 = engine.feed(Gesture::Circle, 2100);
  assert(res3.status == StepStatus::Completed);
  assert(res3.actionTriggered);
  assert(res3.macroId == 1);
  assert(strcmp(res3.macroName, "MACRO_01") == 0);
  assert(res3.actionPayload == 42);
  assert(res3.currentStep == 3);
  assert(g_callbackDispatches == 1);
  assert(g_lastDispatchedId == 1);

  // State machine must reset to idle after completion
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);

  // 4. Invalid transition / unexpected movement cancellation
  // Step 1: Left
  engine.feed(Gesture::Left, 3000);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);

  // Unexpected movement: Down (not matching next step Right)
  StepResult resInvalid = engine.feed(Gesture::Down, 3500);
  assert(resInvalid.status == StepStatus::Cancelled);
  assert(!resInvalid.actionTriggered);
  assert(strcmp(resInvalid.message, "INVALID_TRANSITION") == 0);
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);
  assert(g_callbackDispatches == 1); // No new dispatch

  // 5. Configurable inter-gesture timeout via update()
  engine.setTimeoutMs(1200);
  assert(engine.getTimeoutMs() == 1200);

  engine.feed(Gesture::Left, 5000);
  assert(engine.isInSequence());

  // Tick before timeout
  StepResult tickOk = engine.update(6000); // delta = 1000 <= 1200
  assert(tickOk.status == StepStatus::Progress);
  assert(engine.isInSequence());

  // Tick after timeout
  StepResult tickTimeout = engine.update(6300); // delta = 1300 > 1200
  assert(tickTimeout.status == StepStatus::Timeout);
  assert(!tickTimeout.actionTriggered);
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);

  // 6. Timeout during feed(): gesture starts fresh sequence if valid
  engine.feed(Gesture::Left, 7000);
  assert(engine.isInSequence());

  // Feed Left after timeout (elapsed 2000 > 1200): old sequence expires, new Left starts sequence
  StepResult resFresh = engine.feed(Gesture::Left, 9000);
  assert(resFresh.status == StepStatus::Progress);
  assert(resFresh.currentStep == 1);
  assert(engine.isInSequence());

  // Feed Right after timeout (elapsed 2000 > 1200): old sequence expires, Right cannot start sequence -> Ignored
  StepResult resExpired = engine.feed(Gesture::Right, 11500);
  assert(resExpired.status == StepStatus::Ignored);
  assert(!resExpired.actionTriggered);
  assert(!engine.isInSequence());

  // 7. Cancellation on UNKNOWN gesture
  engine.feed(Gesture::Left, 13000);
  assert(engine.isInSequence());

  // By default, abortOnUnknown is true
  StepResult resUnknown = engine.feed(Gesture::Unknown, 13500);
  assert(resUnknown.status == StepStatus::Cancelled);
  assert(!resUnknown.actionTriggered);
  assert(resUnknown.macroId == 0);
  assert(!engine.isInSequence());
  assert(g_callbackDispatches == 1);

  // When abortOnUnknown is disabled, UNKNOWN is ignored without aborting
  engine.setAbortOnUnknown(false);
  engine.feed(Gesture::Left, 14000);
  assert(engine.isInSequence());

  StepResult resUnknownIgnore = engine.feed(Gesture::Unknown, 14200);
  assert(resUnknownIgnore.status == StepStatus::Ignored);
  assert(!resUnknownIgnore.actionTriggered);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);

  // Complete sequence after ignored unknown
  engine.feed(Gesture::Right, 14400);
  StepResult resFinish = engine.feed(Gesture::Circle, 14600);
  assert(resFinish.status == StepStatus::Completed);
  assert(resFinish.actionTriggered);
  assert(g_callbackDispatches == 2);
  engine.setAbortOnUnknown(true);

  // 8. Manual abort and reset
  engine.feed(Gesture::Left, 16000);
  assert(engine.isInSequence());
  StepResult resAbort = engine.abort();
  assert(resAbort.status == StepStatus::Cancelled);
  assert(!resAbort.actionTriggered);
  assert(!engine.isInSequence());

  // Aborting when idle
  StepResult resAbortIdle = engine.abort();
  assert(resAbortIdle.status == StepStatus::Ignored);
  assert(!resAbortIdle.actionTriggered);

  // 9. Multiple registered macros with prefix sharing
  engine.clearMacros();
  assert(engine.getMacroCount() == 0);
  engine.setTimeoutMs(2000);

  // Macro 1: LEFT -> RIGHT -> CIRCLE (101)
  // Macro 2: LEFT -> RIGHT -> UP (102)
  // Macro 3: UP -> DOWN (103)
  assert(engine.registerMacro(101, "MACRO_LRC", {Gesture::Left, Gesture::Right, Gesture::Circle}));
  assert(engine.registerMacro(102, "MACRO_LRU", {Gesture::Left, Gesture::Right, Gesture::Up}));
  assert(engine.registerMacro(103, "MACRO_UD", {Gesture::Up, Gesture::Down}));
  assert(engine.getMacroCount() == 3);

  // Dispatch Macro 102
  engine.feed(Gesture::Left, 20000);
  engine.feed(Gesture::Right, 20500);
  StepResult resMulti = engine.feed(Gesture::Up, 21000);
  assert(resMulti.status == StepStatus::Completed);
  assert(resMulti.macroId == 102);
  assert(strcmp(resMulti.macroName, "MACRO_LRU") == 0);
  assert(!engine.isInSequence());

  // Dispatch Macro 103
  engine.feed(Gesture::Up, 22000);
  StepResult resUD = engine.feed(Gesture::Down, 22500);
  assert(resUD.status == StepStatus::Completed);
  assert(resUD.macroId == 103);
  assert(strcmp(resUD.macroName, "MACRO_UD") == 0);

  // 10. 32-bit unsigned rollover handling
  engine.clearMacros();
  assert(engine.registerMacro(201, "ROLLOVER_TEST", {Gesture::Left, Gesture::Right}));
  engine.setTimeoutMs(100);

  // Feed step 1 right before 32-bit uint rollover (0xFFFFFFFA = -6)
  uint32_t tNearMax = 0xFFFFFFFAu;
  StepResult resRoll1 = engine.feed(Gesture::Left, tNearMax);
  assert(resRoll1.status == StepStatus::Progress);
  assert(engine.isInSequence());

  // Tick after rollover: nowMs = 0x00000070 (+112). Elapsed = 112 - (-6) = 118 >= 100
  uint32_t tAfterRollover = 0x00000070u;
  StepResult resRollTimeout = engine.update(tAfterRollover);
  assert(resRollTimeout.status == StepStatus::Timeout);
  assert(!engine.isInSequence());

  // 11. Exact boundary timeout test (nowMs - lastGestureTimeMs == timeoutMs)
  engine.setTimeoutMs(500);
  engine.feed(Gesture::Left, 1000);
  assert(engine.isInSequence());
  // Delta = 500 == timeoutMs: must time out
  StepResult resExactTimeout = engine.update(1500);
  assert(resExactTimeout.status == StepStatus::Timeout);
  assert(!engine.isInSequence());

  // 12. Duplicate sequence and prefix collision validation
  engine.clearMacros();
  assert(engine.registerMacro(1, "MACRO_BASE", {Gesture::Left, Gesture::Right, Gesture::Circle}));
  assert(engine.getMacroCount() == 1);

  // Duplicate sequence with different ID: must be rejected
  assert(!engine.registerMacro(2, "MACRO_DUP", {Gesture::Left, Gesture::Right, Gesture::Circle}));
  assert(engine.getMacroCount() == 1);

  // Prefix collision: shorter sequence that is prefix of existing macro
  assert(!engine.registerMacro(3, "MACRO_SHORT_PREFIX", {Gesture::Left, Gesture::Right}));
  assert(engine.getMacroCount() == 1);

  // Prefix collision: longer sequence that extends existing macro
  assert(!engine.registerMacro(4, "MACRO_LONG_EXTENSION", {Gesture::Left, Gesture::Right, Gesture::Circle, Gesture::Up}));
  assert(engine.getMacroCount() == 1);

  // Re-registering existing ID: updates definition in place without increasing count
  assert(engine.registerMacro(1, "MACRO_UPDATED", {Gesture::Up, Gesture::Down}));
  assert(engine.getMacroCount() == 1);
  const MacroDefinition* mUpdated = engine.findMacroById(1);
  assert(mUpdated != nullptr);
  assert(strcmp(mUpdated->name, "MACRO_UPDATED") == 0);
  assert(mUpdated->length == 2);

  // 13. Dynamic unregistration
  assert(engine.unregisterMacro(1));
  assert(engine.getMacroCount() == 0);
  assert(engine.findMacroById(1) == nullptr);
  assert(!engine.unregisterMacro(999)); // Nonexistent ID

  // 14. Clean buffer state on completion and cancellation
  assert(engine.registerMacro(10, "BUF_CHECK", {Gesture::Left, Gesture::Right}));
  engine.feed(Gesture::Left, 1000);
  assert(engine.getCurrentBuffer()[0] == Gesture::Left);
  engine.feed(Gesture::Right, 1100); // Dispatches
  assert(!engine.isInSequence());
  assert(engine.getCurrentBuffer()[0] == Gesture::Unknown); // Buffer zeroed

  // 15. CircleCcw directionality and circle_cw alias
  assert(isDirectional(Gesture::CircleCcw));
  assert(gestureFromString("circle_cw") == Gesture::Circle);

  // 16. Out-of-range gesture enum registration rejection
  Gesture badEnumSeq[] = {static_cast<Gesture>(99), Gesture::Right};
  assert(!engine.registerMacro(301, "BAD_ENUM", badEnumSeq, 2));

  // 17. Unregister macro while active sequence candidate cleans up orphaned sequence
  engine.clearMacros();
  assert(engine.registerMacro(401, "ORPHAN_CANDIDATE", {Gesture::Up, Gesture::Down}));
  engine.feed(Gesture::Up, 5000);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);
  assert(engine.unregisterMacro(401));
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);
  assert(engine.getCurrentBuffer()[0] == Gesture::Unknown);

  // 18. clearMacros() complete state and memory wipe
  assert(engine.registerMacro(501, "WIPE_TEST", {Gesture::Left, Gesture::Right}));
  engine.feed(Gesture::Left, 6000);
  assert(engine.isInSequence());
  engine.clearMacros();
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);
  assert(engine.getLastGestureTimeMs() == 0);
  assert(engine.getCurrentBuffer()[0] == Gesture::Unknown);
  assert(engine.getMacroCount() == 0);

  // 19. Subsequent feed() with default nowMs=0 does not underflow and false timeout
  assert(engine.registerMacro(601, "DEFAULT_TIME", {Gesture::Left, Gesture::Right}));
  StepResult resT1 = engine.feed(Gesture::Left, 10000);
  assert(resT1.status == StepStatus::Progress);
  StepResult resT2 = engine.feed(Gesture::Right); // nowMs omitted (defaults to 0)
  assert(resT2.status == StepStatus::Completed);
  assert(resT2.actionTriggered);

  // 20. update() reports valid expectedTotal while in progress
  engine.setTimeoutMs(2000);
  assert(engine.registerMacro(701, "EXP_TOTAL", {Gesture::Down, Gesture::Up, Gesture::Circle}));
  engine.feed(Gesture::Down, 20000);
  StepResult tickProgress = engine.update(20200);
  assert(tickProgress.status == StepStatus::Progress);
  assert(tickProgress.expectedTotal == 3);
  assert(tickProgress.currentStep == 1);

  // 21. registerMacro in-place update while active sequence is in progress
  // Subcase A: updated sequence has a completely different prefix -> orphan candidate cleaned up
  engine.clearMacros();
  assert(engine.registerMacro(801, "INPLACE_ORPHAN", {Gesture::Left, Gesture::Right}));
  engine.feed(Gesture::Left, 30000);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);
  assert(engine.getCurrentBuffer()[0] == Gesture::Left);
  // Update in place with new sequence starting with Up
  assert(engine.registerMacro(801, "INPLACE_UPDATED", {Gesture::Up, Gesture::Down}));
  assert(!engine.isInSequence());
  assert(engine.getCurrentStep() == 0);
  assert(engine.getCurrentBuffer()[0] == Gesture::Unknown);

  // Subcase B: updated sequence preserves matching prefix -> candidate remains active
  assert(engine.registerMacro(802, "INPLACE_PREFIX", {Gesture::Push, Gesture::Stop}));
  engine.feed(Gesture::Push, 31000);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);
  // Update in place with new sequence also starting with Push
  assert(engine.registerMacro(802, "INPLACE_PREFIX_NEW", {Gesture::Push, Gesture::Circle}));
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);
  StepResult resCont = engine.feed(Gesture::Circle, 31500);
  assert(resCont.status == StepStatus::Completed);
  assert(resCont.macroId == 802);
  assert(strcmp(resCont.macroName, "INPLACE_PREFIX_NEW") == 0);

  // 22. Out-of-range gesture enum fed to MacroEngine::feed
  engine.clearMacros();
  assert(engine.registerMacro(901, "OUT_OF_RANGE_TEST", {Gesture::Left, Gesture::Right}));
  // At step 0: returns Ignored / UNKNOWN_IGNORED
  StepResult resBadIdle = engine.feed(static_cast<Gesture>(99), 40000);
  assert(resBadIdle.status == StepStatus::Ignored);
  assert(strcmp(resBadIdle.message, "UNKNOWN_IGNORED") == 0);
  assert(!resBadIdle.actionTriggered);
  assert(!engine.isInSequence());

  // In active sequence with abortOnUnknown == false: preserves sequence
  engine.setAbortOnUnknown(false);
  engine.feed(Gesture::Left, 41000);
  assert(engine.isInSequence());
  StepResult resBadIgnore = engine.feed(static_cast<Gesture>(99), 41200);
  assert(resBadIgnore.status == StepStatus::Ignored);
  assert(strcmp(resBadIgnore.message, "UNKNOWN_IGNORED") == 0);
  assert(engine.isInSequence());
  assert(engine.getCurrentStep() == 1);

  // In active sequence with abortOnUnknown == true: cancels sequence cleanly
  engine.setAbortOnUnknown(true);
  StepResult resBadAbort = engine.feed(static_cast<Gesture>(99), 41400);
  assert(resBadAbort.status == StepStatus::Cancelled);
  assert(strcmp(resBadAbort.message, "ABORTED_ON_UNKNOWN") == 0);
  assert(!engine.isInSequence());

  puts("Macro and sequence engine native tests passed cleanly.");
  return 0;
}
