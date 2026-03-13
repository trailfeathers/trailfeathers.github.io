-- Migration: enforce at most 4 favorite hikes per user (backward compatibility).

CREATE OR REPLACE FUNCTION check_user_favorite_hikes_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM user_favorite_hikes WHERE user_id = NEW.user_id) >= 4 THEN
    RAISE EXCEPTION 'User can have at most 4 favorite hikes';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_favorite_hikes_limit ON user_favorite_hikes;
CREATE TRIGGER trg_user_favorite_hikes_limit
  BEFORE INSERT ON user_favorite_hikes
  FOR EACH ROW
  EXECUTE FUNCTION check_user_favorite_hikes_limit();
